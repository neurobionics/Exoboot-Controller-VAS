# Description: 
# This file contains a class which calculates gait phase based on the average of recent stride durations.
#
# Author: Varun Satyadev Shetty
# Date: 06/17/2024
# Sensor reading logic modified based on exoboot structure by Max Shepherd
import os, sys, csv, time, copy, threading
import numpy as np
from typing import Type
from itertools import chain
from collections import deque

# # logging from Bertec
sys.path.insert(0, '/home/pi/VAS_exoboot_controller/Reference_Scripts_Bertec_Sync')
from rtplot import client
from ZMQ_PubSub import Subscriber
from BaseExoThread import BaseThread
from utils import MovingAverageFilter
from GroundContact import BertecEstimator
from SoftRTloop import FlexibleTimer, FlexibleSleeper

from constants import RTPLOT_IP, VICON_IP
from constants import DEV_ID_TO_MOTOR_SIGN_DICT, DEV_ID_TO_ANK_ENC_SIGN_DICT
from constants import EFFICIENCY, Kt, ENC_CLICKS_TO_DEG, GYRO_GAIN, ACCEL_GAIN

class GaitStateEstimator(BaseThread):
    def __init__(self, startstamp, device_left, device_right, thread_left, thread_right, name='GSE', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        # Threading
        super().__init__(name=name, daemon=daemon, pause_event=pause_event, quit_event=quit_event)
        self.device_left = device_left
        self.device_right = device_right
        self.device_thread_left = thread_left
        self.device_thread_right = thread_right

        # Peak torques set by GUI
        self.peak_torque_left = 0
        self.peak_torque_right = 0

        # Logging fields
        self.fields = ['pitime', 'forceplate_left', 'forceplate_right', 'thread_freq']
        self.data_dict = dict.fromkeys(self.fields)

        # LoggingNexus
        self.startstamp = startstamp
        self.loggingnexus = None

        # Link to devices
        self.link_to_device()

    def link_to_device(self):
        self.device_left.gse = self
        self.device_right.gse = self

    def set_peak_torque_left(self, T):
        self.peak_torque_left = T
        self.device_thread_left.peak_torque = self.peak_torque_left

    def set_peak_torque_right(self, T):
        self.peak_torque_right = T
        self.device_thread_right.peak_torque = self.peak_torque_right

    def get_sensor_data(self):
        """TODO implement"""
        pass

    def get_estimate(self):
        """TODO implement"""
        pass
    
    def on_pre_run(self):
        """
        Runs once before starting main loop
        """
        # Bertec subscribers and estimators
        self.sub_bertec_right = Subscriber(publisher_ip=VICON_IP,topic_filter='fz_right',timeout_ms=5)
        self.sub_bertec_left = Subscriber(publisher_ip=VICON_IP,topic_filter='fz_left',timeout_ms=5)
        self.bertec_estimator = BertecEstimator(self.sub_bertec_left, self.sub_bertec_right, filter_size=10)

        # RealTimePlotting of: left & right angle angle, actual ankle torque, ankle velocity, and commanded torque
        # client.configure_ip(RTPLOT_IP)
        # # plot_1_config = {'names': ['Ankle Angle Left'], 'title': "Ankle Angle Left", 'colors': ['r'], 'yrange':[20, 130], 'ylabel': "degrees", 'xlabel': 'timestep', "line_width":[8,8]}
        # # plot_5_1_config = {'names': ['Desired Torque Left'], 'title': "Desired Torque Left", 'colors': ['b'], 'yrange':[0,40], 'ylabel': "Nm", 'xlabel': 'timestep',"line_width":[8,8]}
        # # plot_5_1_1_config = {'names': ['Calcd Torque Left'], 'title': "Calcd Torque Left", 'colors': ['r'], 'yrange':[0, 40], 'ylabel': "Nm", 'xlabel': 'timestep',"line_width":[8,8]}
        # # plot_9_config = {'names': ['In Swing Left'], 'title': "Swing Left", 'colors': ['r'], 'yrange':[0, 100], 'ylabel': "degrees", 'xlabel': 'timestep',"line_width":[8,8]}
        # # plot_10_config = {'names': ['Accel Y Left'], 'title': "Accel Y Left", 'colors': ['r'], 'yrange':[-10, 50], 'ylabel': "degrees", 'xlabel': 'timestep',"line_width":[8,8]}
 
        # # all_plot_configs = [plot_1_config, plot_2_config,plot_3_config, plot_3_1_config, plot_4_config, plot_5_config, plot_6_config]
        # all_plot_configs = [plot_1_config, plot_5_1_config, plot_5_1_1_config, plot_9_config, plot_10_config]
        # client.initialize_plots(all_plot_configs)
        
        # Period Tracker
        self.period_tracker = MovingAverageFilter(size=500)
        self.prev_end_time = time.perf_counter()

        # Soft real time loop
        loopFreq = 500 # Hz
        loop_period = 1 / loopFreq
        self.softRTloop = FlexibleSleeper(period=loop_period)

    def pre_iterate(self, pause_event):
        """
        Sensor and Bertec reading
        Runs even if threads are paused
        """
        # Set starting time stamp
        self.data_dict['pitime'] = time.perf_counter() - self.startstamp

        # TODO IMU Estimation
        # self.get_sensor_data()
        # self.get_estimate()

        new_stride_flag_left, new_stride_flag_right, force_left, force_right = self.bertec_estimator.get_estimate(pause_event)

        # Add forces to data dict
        self.data_dict['forceplate_left'] = force_left
        self.data_dict['forceplate_right'] = force_right

        return new_stride_flag_left, new_stride_flag_right

    def iterate(self, new_stride_flag_left, new_stride_flag_right):
        """
        Update device estimates
        Does not run when threads paused
        """
        # Update exoboot threads if new state estimate
        if new_stride_flag_left:
            HS_l, stride_period_l, in_swing_l = self.bertec_estimator.return_estimate_left()
            self.device_thread_left.set_state_estimate(HS_l, stride_period_l, self.peak_torque_left, in_swing_l)

        if new_stride_flag_right:
            HS_r, stride_period_r, in_swing_r = self.bertec_estimator.return_estimate_right()
            self.device_thread_right.set_state_estimate(HS_r, stride_period_r, self.peak_torque_right, in_swing_r)
        
    def post_iterate(self):
        """
        Loop period tracking and soft real time pause
        """
        # Update Period Tracker
        end_time = time.perf_counter()
        self.period_tracker.update(end_time - self.prev_end_time)
        self.prev_end_time = end_time
        my_freq = 1/self.period_tracker.average()

        # Log gse freq
        self.data_dict['thread_freq'] = my_freq
        if self.loggingnexus and self.pause_event.is_set():
            self.loggingnexus.append(self.name, copy.deepcopy(self.data_dict))

        # soft real-time loop
        self.softRTloop.pause()

    def run(self):
        """
        Custom run to continue catching heelstrike but not update estimates
        """
        self.on_pre_run()
        while self.quit_event.is_set():
            nslf, nsfr = self.pre_iterate(self.pause_event)
            if self.pause_event.is_set():
                self.iterate(nslf, nsfr)
            self.post_iterate()
        self.on_pre_exit()
