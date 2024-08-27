# Description: 
# This file contains a class which calculates gait phase based on the average of recent stride durations.
#
# Author: Varun Satyadev Shetty
# Date: 06/17/2024
# Sensor reading logic modified based on exoboot structure by Max Shepherd

import sys
import csv
import time
import threading
import numpy as np
from typing import Type
from rtplot import client

# # logging from Bertec
sys.path.insert(0, '/home/pi/VAS_exoboot_controller/Reference_Scripts_Bertec_Sync')
from ZMQ_PubSub import Subscriber
from BaseExoThread import BaseThread
from utils import MovingAverageFilter
from GroundContact import BertecEstimator
from SoftRTloop import FlexibleTimer, FlexibleSleeper

import config
from constants import RTPLOT_IP, VICON_IP
from constants import DEV_ID_TO_MOTOR_SIGN_DICT, DEV_ID_TO_ANK_ENC_SIGN_DICT
from constants import EFFICIENCY, Kt, ENC_CLICKS_TO_DEG, GYRO_GAIN, ACCEL_GAIN

class GaitStateEstimator(BaseThread):
    def __init__(self, device_left, device_right, thread_left, thread_right, name='GSE', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        # Threading
        super().__init__(name=name, daemon=daemon, pause_event=pause_event, quit_event=quit_event)

        self.device_left = device_left
        self.device_right = device_right
        self.device_thread_left = thread_left
        self.device_thread_right = thread_right

        # Encoder/Motor signs
        self.ank_enc_sight_left = DEV_ID_TO_ANK_ENC_SIGN_DICT[device_left.id]
        self.ank_enc_sight_right = DEV_ID_TO_ANK_ENC_SIGN_DICT[device_right.id]
        self.motor_sign_left = DEV_ID_TO_MOTOR_SIGN_DICT[device_left.id]
        self.motor_sign_right = DEV_ID_TO_MOTOR_SIGN_DICT[device_right.id]
       
        # Temp variables
        self.prev_accel_y_left = 0
        self.prev_time_left = 0
        self.prev_accel_y_right = 0
        self.prev_time_right = 0
        self.prev_accel_x_left = 0
        self.prev_accel_x_right = 0

        # Stride time
        self.stride_time_left = [1, 1]
        self.stride_time_right = [1, 1]

        self.start_time_left = 0
        self.stride_time_left_temp = 0
        self.start_time_right = 0
        self.stride_time_right_temp = 0

        self.time_in_current_stride_left = 0
        self.time_in_current_stride_right = 0

        self.left_prev_hs = False
        self.right_prev_hs = False
        
        # Stance time
        self.stance_time_left = [1, 1]
        self.stance_time_right = [1, 1]
        self.stance_time_left_temp = 0
        self.stance_time_right_temp = 0

        ## Set the Filename to Save the Logged Data: 
        fname_construction = 'Sub{0}_{1}_{2}_{3}.csv'.format(
            str(config.subject_ID), 
            str(config.trial_type), 
            str(config.trial_presentation), 
            time.strftime("%m%d%Y")
        )
        self.filename = '/home/pi/VAS_exoboot_controller/Experimental_Logs/' + str(fname_construction)

        """New Stuff"""
        # Bertec
        self.sub_bertec_right = Subscriber(publisher_ip=VICON_IP,topic_filter='fz_right',timeout_ms=5)
        self.sub_bertec_left = Subscriber(publisher_ip=VICON_IP,topic_filter='fz_left',timeout_ms=5)

        self.bertec_estimator = BertecEstimator(self.sub_bertec_left, self.sub_bertec_right, filter_size=10)

        # Set By GUI
        self.peak_torque_left = 0
        self.peak_torque_right = 0
        
        # Flexible Timer
        loopFreq = 300 #425 # Hz
        loop_period = 1 / loopFreq
        self.softRTloop = FlexibleSleeper(period=loop_period)
    
    def set_peak_torque_left(self, T):
        self.peak_torque_left = T

    def set_peak_torque_right(self, T):
        self.peak_torque_right = T

    def read_exo_sensors(self):
        data_left = self.device_left.read()
        ##### Time #####
        config.state_time_left = data_left['state_time'] / 1000 #converting to seconds
        
        ##### Temperature #####
        config.temperature_left = data_left['temperature']

        ##### Ankle Encoder #####
        #TODO: Need to add if loop to give error message if the ankle angle excceds the maximum and min angle angles
        config.ankle_angle_left = (self.ank_enc_sight_left * data_left['ank_ang'] * ENC_CLICKS_TO_DEG) - config.max_dorsiflexed_ang_left  # obtain ankle angle in deg wrt max dorsi offset
        ##### IMU #####
        #left accel
        #Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
        config.accel_x_left = data_left['accelx'] * ACCEL_GAIN  #This is in the walking direction {i.e the rotational axis of the frontal plane}
        config.accel_y_left = -1 * data_left['accely'] * ACCEL_GAIN # This is in the vertical direction {i.e the rotational axis of the transverse plane}
        config.accel_z_left = data_left['accelz'] * ACCEL_GAIN # This is the rotational axis of the sagital plane

        # Left gyro
        # Note based on the MPU reading script it says the gyro = radians(raw_gyro/gyroscale) for the gyrorange of 1000DPS the gyroscale is 32.8
        config.gyro_x_left = -1 * data_left['gyrox'] * GYRO_GAIN
        config.gyro_y_left = data_left['gyroy'] * GYRO_GAIN
        # Remove -1 for EB-51
        config.gyro_z_left = data_left['gyroz'] * GYRO_GAIN

        ##### Motor #####
        # Left
        config.motor_angle_left = self.motor_sign_left * data_left['mot_ang'] * ENC_CLICKS_TO_DEG
        config.motor_velocity_left = data_left['mot_vel']
        config.ankle_velocity_left = data_left['ank_vel'] / 10
        config.motor_current_left = data_left['mot_cur']
        
        
        ## ====Calculate Delivered Ankle Torque from Measured Current====
        act_mot_torque_left = (config.motor_current_left * Kt / 1000 / self.motor_sign_left)  # Nm
        config.act_ank_torque_left = act_mot_torque_left * config.N_left * EFFICIENCY

        """Read Right exo"""
        data_right = self.device_right.read()

        ##### Time #####
        config.state_time_right = data_right['state_time'] / 1000 # converting to seconds
        
        ##### Temperature #####
        config.temperature_right = data_right['temperature']
        
        ##### Ankle Encoder #####
        #TODO: Need to add if loop to give error message if the ankle angle excceds the maximum and min ale angles
        config.ankle_angle_right = (self.ank_enc_sight_right * data_right['ank_ang'] * ENC_CLICKS_TO_DEG) - config.max_dorsiflexed_ang_right  # obtain ankle angle in deg wrt max dorsi offset

        ##### IMU #####
        # Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
        # Right accel
        config.accel_x_right = data_right['accelx'] * ACCEL_GAIN  #This is in the walking direction {i.e the rotational axis of the frontal plane} 
        config.accel_y_right = -1 * data_right['accely'] * ACCEL_GAIN # This is in the vertical direction {i.e the rotational axis of the transverse plane}
        config.accel_z_right = data_right['accelz'] * ACCEL_GAIN # This is the rotational axis of the sagital plane
        
        # Right gyro
        config.gyro_x_right = data_right['gyrox'] * GYRO_GAIN
        config.gyro_y_right = data_right['gyroy'] * GYRO_GAIN
        config.gyro_z_right = data_right['gyroz'] * GYRO_GAIN

        ##### Motor #####
        # Right
        config.motor_angle_right = self.motor_sign_right*data_right['mot_ang'] *ENC_CLICKS_TO_DEG
        config.motor_velocity_right = data_right['mot_vel']
        config.ankle_velocity_right = data_right['ank_vel'] / 10
        
        config.motor_current_right = data_right['mot_cur']
            
        ## ====Calculate Delivered Ankle Torque from Measured Current====
        act_mot_torque_right = (config.motor_current_right * Kt / 1000 / self.motor_sign_right)  # in Nm
        config.act_ank_torque_right = act_mot_torque_right * config.N_right * EFFICIENCY

    def gait_estimator(self):
        pass
            
    def in_swing_flag(self):
        pass
                
    def IMU_stance_time(self, side):
        pass
    
    def stride_time(self):
        pass
    
    def logging(self, filename, datapoint_array): #Adding VSO/ VSPA style of logging
        with open(filename, 'a') as f:
            writer = csv.writer(f, lineterminator='\n',quotechar='|')
            writer.writerow(datapoint_array)
    
    def on_pre_run(self):
        """
        Run Once before starting main loop
        """
        # RealTimePlotting of: left & right angle angle, actual ankle torque, ankle velocity, and commanded torque
        client.configure_ip(RTPLOT_IP)
        plot_1_config = {'names': ['Ankle Angle Left'], 'title': "Ankle Angle Left", 'colors': ['r'], 'yrange':[20, 130], 'ylabel': "degrees", 'xlabel': 'timestep', "line_width":[8,8]}
        # plot_2_config = {'names': ['Ankle Angle Right'], 'title': "Ankle Angle Right", 'colors': ['r'], 'yrange':[20,130], 'ylabel': "degrees", 'xlabel': 'timestep'}
        # plot_3_config = {'names': ['Left Motor encoder'], 'title': "Left Motor Angle", 'colors': ['b'], 'yrange':[0,1200], 'ylabel': "degrees", 'xlabel': 'timestep'}
        # plot_4_config = {'names': ['Right Motor encoder'], 'title': "Left Motor Angle", 'colors': ['b'], 'yrange':[0,1200], 'ylabel': "degrees", 'xlabel': 'timestep'}        
        # plot_3_config = {'names': ['Left Motor Current'], 'title': "Left Motor Current", 'colors': ['b'], 'yrange':[0,25000], 'ylabel': "Nm", 'xlabel': 'timestep'}
        # plot_3_1_config = {'names': ['Right Motor Current'], 'title': "Right Motor Current", 'colors': ['b'], 'yrange':[0,25000], 'ylabel': "Nm", 'xlabel': 'timestep'}
        plot_5_1_config = {'names': ['Desired Torque Left'], 'title': "Desired Torque Left", 'colors': ['b'], 'yrange':[0,40], 'ylabel': "Nm", 'xlabel': 'timestep',"line_width":[8,8]}
        plot_5_1_1_config = {'names': ['Calcd Torque Left'], 'title': "Calcd Torque Left", 'colors': ['r'], 'yrange':[0, 40], 'ylabel': "Nm", 'xlabel': 'timestep',"line_width":[8,8]}
        # plot_5_2_config = {'names': ['Desired Torque Right'], 'title': "Desired Torque Right", 'colors': ['b'], 'yrange':[0,20], 'ylabel': "Nm", 'xlabel': 'timestep'}
        # plot_6_config = {'names': ['Desired Torque Right'], 'title': "LEFT CURRENT TIME", 'colors': ['b'], 'yrange':[0,5], 'ylabel': "Nm", 'xlabel': 'timestep'}
        # plot_6_1_config = {'names': ['N Left'], 'title': "N Left", 'colors': ['b'], 'yrange':[-10,20], 'ylabel': "TR", 'xlabel': 'timestep',"line_width":[8,8]}
        # plot_6_2_config = {'names': ['N Right'], 'title': "N Right", 'colors': ['r'], 'yrange':[-10,18], 'ylabel': "TR", 'xlabel': 'timestep'}
        
        # plot_7_config = {'names': ['Accel X Backward Left'], 'title': "Accel X Left", 'colors': ['r'], 'yrange':[-10, 50], 'ylabel': "degrees", 'xlabel': 'timestep',"line_width":[8,8]}
        # plot_8_config = {'names': ['Gyro Z Left'], 'title': "Gyro Z Left", 'colors': ['b'], 'yrange':[-50, 50], 'ylabel': "degrees", 'xlabel': 'timestep', "line_width":[8,8]}
        plot_9_config = {'names': ['In Swing Left'], 'title': "Swing Left", 'colors': ['r'], 'yrange':[0, 100], 'ylabel': "degrees", 'xlabel': 'timestep',"line_width":[8,8]}
        plot_10_config = {'names': ['Accel Y Left'], 'title': "Accel Y Left", 'colors': ['r'], 'yrange':[-10, 50], 'ylabel': "degrees", 'xlabel': 'timestep',"line_width":[8,8]}
        # plot_12_config = {'names': ['Calcd Torque Right'], 'title': "Calcd Torque Right", 'colors': ['r'], 'yrange':[0, 40], 'ylabel': "Nm", 'xlabel': 'timestep',"line_width":[8,8]}
 
        # all_plot_configs = [plot_1_config, plot_2_config,plot_3_config, plot_3_1_config, plot_4_config, plot_5_config, plot_6_config]
        all_plot_configs = [plot_1_config, plot_5_1_config, plot_5_1_1_config, plot_9_config, plot_10_config]
        client.initialize_plots(all_plot_configs)
        
        # Logging to csv
        self.logging(self.filename, ['state_time_left', 'temperature_left', 'ankle_angle_left', 'accel_x_left', 
                         'accel_y_left', 'accel_z_left', 'gyro_x_left', 'gyro_y_left', 'gyro_z_left', 
                         'motor_angle_left', 'motor_velocity_left', 'motor_current_left', 
                         'stride_time_left', 'heel_strike_left', 'time_in_current_stride_left', 'state_time_right', 'temperature_right', 
                         'ankle_angle_right', 'accel_x_right', 'accel_y_right', 'accel_z_right', 
                         'gyro_x_right', 'gyro_y_right', 'gyro_z_right', 'motor_angle_right', 
                         'motor_velocity_right', 'motor_current_right', 'stride_time_right', 
                         'heel_strike_right', 'time_in_current_stride_right', 'rise_time','peak time','fall time', 
                         'peak torque magnitude', 'adjusted slider btn', 'adjusted slider value', 'GUI confirm btn status',
                         'N_left','N_right', 'left_swing_flag', 'right_swing_flag','back_calcd_torque_left','back_calcd_torque_right',
                         'bertec_HS_left', 'bertec_HS_right', 'all_bertec_left', 'all_bertec_right', 'bertec_stance_t_left', 'bertec_stance_t_right',
                         'stride_t_bertec_left', 'stride_t_bertec_right', 'bertec_in_swing_left', 'bertec_in_swing_right',
                         'desired_torque_left', 'desired_torque_right',
                         'vas_main_frequency', 'gui_communication_thread_frequency', 'gse_thread_frequency', 'bertec_thread_frequency'
                         ])
        
        # Period Tracker
        self.period_tracker = MovingAverageFilter(size=500)
        self.prev_end_time = time.time()

    def on_pre_pause(self):
        """
        Runs once when paused
        """
        print("{} is paused".format(self.name))

    def iterate(self):
        """
        Runs when not paused
        """
        # TODO IMU Estimation
        self.read_exo_sensors()
        # self.gait_estimator()
        # self.stride_time()
        # self.in_swing_flag()
        # self.IMU_stance_time()

        # Bertec Estimation: Flag indicates if estimate has changed
        new_stride_flag_left, new_stride_flag_right = self.bertec_estimator.get_estimate()
        # new_stride_flag_left = False
        # new_stride_flag_right = False

        # Update exoboot threads if new state estimate
        if new_stride_flag_left:
            HS_l, stride_period_l, in_swing_l = self.bertec_estimator.return_estimate_left()
            self.device_thread_left.set_state_estimate(HS_l, stride_period_l, self.peak_torque_left, in_swing_l)
        if new_stride_flag_right:
            HS_r, stride_period_r, in_swing_r = self.bertec_estimator.return_estimate_right()
            self.device_thread_right.set_state_estimate(HS_r, stride_period_r, self.peak_torque_right, in_swing_r)
        
        # logging to csv
        # self.logging(self.filename, [config.state_time_left, config.temperature_left, config.ankle_angle_left, config.accel_x_left,
        #     config.accel_y_left, config.accel_z_left, config.gyro_x_left, config.gyro_y_left, config.gyro_z_left,
        #     config.motor_angle_left, config.motor_velocity_left, config.motor_current_left, config.stride_time_left,
        #     config.heel_strike_left, config.time_in_current_stride_left, config.state_time_right, config.temperature_right,
        #     config.ankle_angle_right, config.accel_x_right, config.accel_y_right, config.accel_z_right, config.gyro_x_right,
        #     config.gyro_y_right, config.gyro_z_right, config.motor_angle_right, config.motor_velocity_right,
        #     config.motor_current_right, config.stride_time_right, config.heel_strike_right,
        #     config.time_in_current_stride_right, config.t_rise, config.t_peak, config.t_fall,
        #     config.GUI_commanded_torque, config.adjusted_slider_btn, config.adjusted_slider_value, config.confirm_btn_pressed, 
        #     config.N_left, config.N_right, config.swing_val_left, config.swing_val_right, config.act_ank_torque_left, config.act_ank_torque_right,
        #     config.bertec_HS_left,config.bertec_HS_right, config.z_forces_left, config.z_forces_right, config.time_in_current_stance_left, config.time_in_current_stance_right,
        #     config.stride_period_bertec_left, config.stride_period_bertec_right,config.swing_val_bertec_left,config.swing_val_bertec_right,
        #     config.desired_spline_torque_left,config.desired_spline_torque_right,
        #     config.vas_main_frequency, config.gui_communication_thread_frequency, config.gse_thread_frequency, config.bertec_thread_frequency
        #     ])

        # # plotting with RTPlot
        # #data = [config.ankle_angle_left,config.ankle_angle_right,config.motor_current_left, config.motor_current_right, config.desired_spline_torque_left, config.desired_spline_torque_right, self.time_in_current_stride_left]
        # data = [config.ankle_angle_left, config.desired_spline_torque_left, config.act_ank_torque_left,
        #         config.swing_val_left, config.swing_val_right, config.accel_y_left]
        # client.send_array(data)
        # time.sleep(1/500) 
        
        # Update Period Tracker and config
        end_time = time.time()
        self.period_tracker.update(end_time - self.prev_end_time)
        self.prev_end_time = end_time
        # config.gse_thread_frequency = 1/self.period_tracker.average()

        # soft real-time loop
        self.softRTloop.pause()
