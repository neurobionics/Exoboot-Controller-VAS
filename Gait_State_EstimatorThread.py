# Description: 
# This file contains a class which calculates gait phase based on the average of recent stride durations.
#
# Author: Varun Satyadev Shetty
# Date: 06/17/2024
# Sensor reading logic modified based on exoboot structure by Max Shepherd

import numpy as np
from typing import Type
from collections import deque
import time
import config
from rtplot import client 
import threading
import csv
from time import strftime
from flexsea.device import Device

from SoftRTloop import FlexibleTimer
from utils import MovingAverageFilter

class Gait_State_Estimator(threading.Thread):
    def __init__(self, side_1, device_1, side_2, device_2, quit_event=Type[threading.Event],name='GSE'):
        super().__init__(name = name)

        # Side dependent attributes
        if side_1 == "left":
            self.device_left = device_1
            self.device_right = device_2
            self.motor_sign_left = -1
            self.motor_sign_right = -1
        else:
            self.device_left = device_2
            self.device_right = device_1
            self.motor_sign_left = -1
            self.motor_sign_right = -1

        self.quit_event = quit_event
       
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
            strftime("%m%d%Y")
        )
        self.filename = '/home/pi/Exoboot-Controller-VAS/Experimental_Logs/' + str(fname_construction)
        
        # instantiate soft real-time loop
        loopFreq = 300 #425 # Hz
        self.softRTloop = FlexibleTimer(target_freq=loopFreq) 
        
    def read_exo_sensors(self):
            data_left = self.device_left.read()
            ##### Time #####
            config.state_time_left = data_left['state_time'] / 1000 #converting to seconds
            
            ##### Temperature #####
            config.temperature_left = data_left['temperature']

            ##### Ankle Encoder #####
            #TODO: Need to add if loop to give error message if the ankle angle excceds the maximum and min angle angles
            config.ankle_angle_left = (config.ANK_ENC_SIGN_LEFT_EXO * data_left['ank_ang'] * config.ENC_CLICKS_TO_DEG) - config.max_dorsiflexed_ang_left  # obtain ankle angle in deg wrt max dorsi offset
            ##### IMU #####
            #left accel
            #Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
            config.accel_x_left = data_left['accelx'] * config.ACCEL_GAIN  #This is in the walking direction {i.e the rotational axis of the frontal plane}
            config.accel_y_left = -1 * data_left['accely'] * config.ACCEL_GAIN # This is in the vertical direction {i.e the rotational axis of the transverse plane}
            config.accel_z_left = data_left['accelz'] * config.ACCEL_GAIN # This is the rotational axis of the sagital plane

            # Left gyro
            # Note based on the MPU reading script it says the gyro = radians(raw_gyro/gyroscale) for the gyrorange of 1000DPS the gyroscale is 32.8
            config.gyro_x_left = -1 * data_left['gyrox'] * config.GYRO_GAIN
            config.gyro_y_left = data_left['gyroy'] * config.GYRO_GAIN
            # Remove -1 for EB-51
            config.gyro_z_left = data_left['gyroz'] * config.GYRO_GAIN #-1 * motor_sign * actpack_data.gyroz * constants.GYRO_GAIN  # sign may be different from Max's device

            ##### Motor #####
            # Left
            config.motor_angle_left = self.motor_sign_left * data_left['mot_ang'] * config.ENC_CLICKS_TO_DEG
            config.motor_velocity_left = data_left['mot_vel']
            config.ankle_velocity_left = data_left['ank_vel'] / 10
            config.motor_current_left = data_left['mot_cur']
            
            
            ## ====Calculate Delivered Ankle Torque from Measured Current====
            act_mot_torque_left = (config.motor_current_left * config.Kt / 1000 / self.motor_sign_left)  # in Nm
            config.act_ank_torque_left = act_mot_torque_left * config.N_left * config.efficiency

            """Read Right exo"""
            data_right = self.device_right.read()

            ##### Time #####
            config.state_time_right = data_right['state_time'] *(1/1000) #converting to seconds
            
            ##### Temperature #####
            config.temperature_right = data_right['temperature']
            
            ##### Ankle Encoder #####
            #TODO: Need to add if loop to give error message if the ankle angle excceds the maximum and min ale angles
            config.ankle_angle_right = (config.ANK_ENC_SIGN_RIGHT_EXO*data_right['ank_ang'] * config.ENC_CLICKS_TO_DEG) - config.max_dorsiflexed_ang_right  # obtain ankle angle in deg wrt max dorsi offset

            ##### IMU #####
            # Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
            # Right accel
            config.accel_x_right = data_right['accelx'] * config.ACCEL_GAIN  #This is in the walking direction {i.e the rotational axis of the frontal plane} 
            config.accel_y_right = -1 * data_right['accely'] * config.ACCEL_GAIN # This is in the vertical direction {i.e the rotational axis of the transverse plane}
            config.accel_z_right = data_right['accelz'] * config.ACCEL_GAIN # This is the rotational axis of the sagital plane
            
            # Right gyro
            config.gyro_x_right = data_right['gyrox'] * config.GYRO_GAIN
            config.gyro_y_right = data_right['gyroy'] * config.GYRO_GAIN
            config.gyro_z_right = data_right['gyroz'] * config.GYRO_GAIN

            ##### Motor #####
            # Right
            config.motor_angle_right = self.motor_sign_right*data_right['mot_ang'] *config.ENC_CLICKS_TO_DEG#motor_sign*(data_right.mot_ang - config.motor_angle_offset_right)
            config.motor_velocity_right = data_right['mot_vel']
            config.ankle_velocity_right = data_right['ank_vel'] / 10
            
            config.motor_current_right = data_right['mot_cur']
                
            ## ====Calculate Delivered Ankle Torque from Measured Current====
            act_mot_torque_right = (config.motor_current_right * config.Kt / 1000 / self.motor_sign_right)  # in Nm
            config.act_ank_torque_right = act_mot_torque_right * config.N_right * config.efficiency

    def gait_estimator(self):
            # Left side
            if(abs(config.accel_y_left - self.prev_accel_y_left) >= 1.2 and ((time.time() - self.prev_time_left)>= 0.45)):
                config.heel_strike_left = 10
                config.in_swing_start_left = False
                config.swing_val_left = 10
                self.prev_time_left = time.time()
                # print("Heel Strike Left")
            else:
                config.heel_strike_left = 0
            self.prev_accel_y_left = config.accel_y_left

            # Right side
            if(abs(config.accel_y_right - self.prev_accel_y_right) >= 1.2 and ((time.time() - self.prev_time_right)>= 0.45)):
                config.heel_strike_right = 10
                config.in_swing_start_right = False
                config.swing_val_right = 10
                self.prev_time_right = time.time()
                # print("Heel Strike Right")
            else:
                config.heel_strike_right = 0
            self.prev_accel_y_right = config.accel_y_right
            
    def in_swing_flag(self):
        # Left Side
        if (config.accel_y_left <= 0.8) and (config.ankle_angle_left - config.ankle_offset_left > 10) and (config.gyro_z_left >= -20):
            config.in_swing_start_left = True
            config.swing_val_left = 100

        # Right Side
        if (config.accel_y_right <= 0.8) and (config.ankle_angle_right - config.ankle_offset_right > 10) and (config.gyro_z_right >= -20):
            config.in_swing_start_right = True
            config.swing_val_right = 100
                
    def IMU_stance_time(self, side):
        # compute time spent in stance phase - between heel strike and toe off - in a similar way to stride time
        if (side == 'left'):
            if (config.heel_strike_left == 10 and config.in_swing_start_left == False):
                self.start_time_stance_left = time.time()
                
                if((0.6*config.stance_time_left) <= self.stance_time_left_temp <= (1.2*config.stance_time_left)):
                    self.stance_time_left.append(self.stance_time_left_temp)
                    config.stance_time_left = np.mean(self.stance_time_left[-5:])
                    
            elif (config.heel_strike_left == 0 and config.in_swing_start_left == True):
                self.stance_time_left_temp = time.time() - self.start_time_stance_left
                
            else:
                self.time_in_current_stance_left = time.time() - self.start_time_stance_left
                
            config.time_in_current_stance_left = self.time_in_current_stance_left

        elif(side == 'right'):
            if (config.heel_strike_right == 10 and config.in_swing_start_right == False):
                # stop timer and log time if heel strike is detected and we are not in swing
                self.stance_time_right_temp = time.time()
                if((0.6*config.stance_time_right) <= self.stance_time_right_temp <= (1.2*config.stance_time_right)):
                    self.stance_time_right.append(self.stance_time_right_temp)
                    config.stance_time_right = np.mean(self.stance_time_right[-5:])
                    
                elif (config.heel_strike_right == 0 and config.in_swing_start_right == True):
                    self.start_time_stance_right = time.time() - self.start_time_stance_left
                    
                else:
                    self.time_in_current_stance_right = time.time() - self.start_time_stance_right
                    
                config.time_in_current_stance_right = self.time_in_current_stance_right
           
    # TODO: Debug why this resets mid stance/swing
    def stride_time(self):
        # Left side
        if(config.heel_strike_left == 10 and self.left_prev_hs == True):
            self.stride_time_left_temp = time.time() - self.start_time_left
            # prev thresh: 0.45 & 1.8
            if((0.6*config.stride_time_left) <= self.stride_time_left_temp <= (1.2*config.stride_time_left)):
                self.stride_time_left.append(self.stride_time_left_temp)
                config.stride_time_left = np.mean(self.stride_time_left[-5:])
            self.start_time_left = time.time()
            
        elif(config.heel_strike_left == 10 and self.left_prev_hs == False):
            # First time heel strike is detected
            self.start_time_left = time.time()
            self.left_prev_hs = True
            
        self.time_in_current_stride_left = time.time() - self.start_time_left
        config.time_in_current_stride_left = self.time_in_current_stride_left

        # Right side
        if(config.heel_strike_right == 10 and self.right_prev_hs == True):
            self.stride_time_right_temp = time.time() - self.start_time_right
            # print(self.stride_time_right_temp)
            if((0.6*config.stride_time_right) <= self.stride_time_right_temp <= (1.2*config.stride_time_right)):
                self.stride_time_right.append(self.stride_time_right_temp)
                config.stride_time_right = np.mean(self.stride_time_right[-5:])
            self.start_time_right = time.time()
            
        elif(config.heel_strike_right == 10 and self.right_prev_hs == False):
            # First time heel strike is detected
            self.start_time_right = time.time()
            self.right_prev_hs = True
            
        self.time_in_current_stride_right = time.time() - self.start_time_right
        config.time_in_current_stride_right = self.time_in_current_stride_right
    
    def logging(self, filename, datapoint_array): #Adding VSO/ VSPA style of logging
        with open(filename, 'a') as f:
            writer = csv.writer(f, lineterminator='\n',quotechar='|')
            writer.writerow(datapoint_array)
            
    def run(self):
        # RealTimePlotting of: left & right angle angle, actual ankle torque, ankle velocity, and commanded torque
        client.configure_ip(config.rtplot_ip)
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
        period_tracker = MovingAverageFilter(size=500)
        prev_end_time = time.time()

        while self.quit_event.is_set():
                
                # Running the GSE
                self.read_exo_sensors()
                self.gait_estimator()
                self.stride_time()
                self.in_swing_flag()
                # self.IMU_stance_time()
                
                # logging to csv
                self.logging(self.filename, [config.state_time_left, config.temperature_left, config.ankle_angle_left, config.accel_x_left,
                    config.accel_y_left, config.accel_z_left, config.gyro_x_left, config.gyro_y_left, config.gyro_z_left,
                    config.motor_angle_left, config.motor_velocity_left, config.motor_current_left, config.stride_time_left,
                    config.heel_strike_left, config.time_in_current_stride_left, config.state_time_right, config.temperature_right,
                    config.ankle_angle_right, config.accel_x_right, config.accel_y_right, config.accel_z_right, config.gyro_x_right,
                    config.gyro_y_right, config.gyro_z_right, config.motor_angle_right, config.motor_velocity_right,
                    config.motor_current_right, config.stride_time_right, config.heel_strike_right,
                    config.time_in_current_stride_right, config.t_rise, config.t_peak, config.t_fall,
                    config.GUI_commanded_torque, config.adjusted_slider_btn, config.adjusted_slider_value, config.confirm_btn_pressed, 
                    config.N_left, config.N_right, config.swing_val_left, config.swing_val_right, config.act_ank_torque_left, config.act_ank_torque_right,
                    config.bertec_HS_left,config.bertec_HS_right, config.z_forces_left, config.z_forces_right, config.time_in_current_stance_left, config.time_in_current_stance_right,
                    config.stride_period_bertec_left, config.stride_period_bertec_right,config.swing_val_bertec_left,config.swing_val_bertec_right,
                    config.desired_spline_torque_left,config.desired_spline_torque_right,
                    config.vas_main_frequency, config.gui_communication_thread_frequency, config.gse_thread_frequency, config.bertec_thread_frequency
                    ])

                # plotting with RTPlot
                #data = [config.ankle_angle_left,config.ankle_angle_right,config.motor_current_left, config.motor_current_right, config.desired_spline_torque_left, config.desired_spline_torque_right, self.time_in_current_stride_left]
                data = [config.ankle_angle_left, config.desired_spline_torque_left, config.act_ank_torque_left,
                        config.swing_val_left, config.swing_val_right, config.accel_y_left]
                client.send_array(data)
                # time.sleep(1/500) 
                
                # Update Period Tracker and config
                end_time = time.time()
                period_tracker.update(end_time - prev_end_time)
                prev_end_time = end_time
                config.gse_thread_frequency = 1/period_tracker.average()

                # soft real-time loop
                self.softRTloop.pause()
            # except Exception as e:
            #     print('Error in the Gait State Estimator thread!!!!')
            #     print(e)

"""#Testing GSE, very basic script

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe
import config
import threading


def main_loop_simulation(fxs):
    while True:
        fxs.start_streaming(dev_id=dev_id_1,freq=200, log_en=False)
        fxs.start_streaming(dev_id=dev_id_2,freq=200, log_en=False)
        time.sleep(1/100)

if __name__ == '__main__':
    fxs = flex.FlexSEA()
    ports = ['/dev/ttyACM0', '/dev/ttyACM1']
    dev_id_1 = fxs.open(ports[0], config.BAUD_RATE, log_level=3)
    dev_id_2 = fxs.open(ports[1], config.BAUD_RATE, log_level=3)


    lock = threading.Lock()
    quit_event = threading.Event()
    quit_event.set()
    g = Gait_State_Estimator(fxs, dev_id_1, dev_id_2, quit_event=quit_event)
    g.daemon= True
    g.start()
    main_loop_simulation(fxs)
    time.sleep(1/100)
    g.join()
    lock.acquire()"""