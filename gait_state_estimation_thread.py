# Description:
# This file contains a class which calculates gait phase based on the average of recent stride durations.
#
# Author: Varun Satyadev Shetty
# Date: 06/17/2024
# Sensor reading logic modified based on exoboot structure by Max Shepherd
import time, copy, threading
import datetime
from typing import Type

# from rtplot import client
from src.gait_state_estimation.ZMQ_PubSub import Subscriber
from base_exo_thread import BaseThread
from src.utils.filter_utils import MovingAverageFilter
from src.gait_state_estimation.gse_bertec import BertecEstimator
from src.utils.SoftRTloop import FlexibleSleeper

from src.settings.constants import *


class GaitStateEstimator(BaseThread):
    """
    Description
    """

    def __init__(
        self,
        startstamp,
        device_left,
        device_right,
        thread_left,
        thread_right,
        name="GSE",
        filter_size=10,
        daemon=True,
        continuousmode=False,
        quit_event=Type[threading.Event],
        pause_event=Type[threading.Event],
        log_event=Type[threading.Event],
    ):
        super().__init__(name, daemon, quit_event, pause_event, log_event)
        self.device_left = device_left
        self.device_right = device_right
        self.device_thread_left = thread_left
        self.device_thread_right = thread_right

        # Filter size
        self.filter_size = filter_size

        # Operating mode
        self.continuousmode = continuousmode

        # Peak torques set by GUI
        self.peak_torque_left = 0
        self.peak_torque_right = 0

        # Logging fields
        self.fields = GSETHREAD_FIELDS
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
        if self.continuousmode:
            self.device_thread_left.set_peak_torque(self.peak_torque_left)

    def set_peak_torque_right(self, T):
        self.peak_torque_right = T
        if self.continuousmode:
            self.device_thread_right.set_peak_torque(self.peak_torque_right)

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
        self.sub_bertec_right = Subscriber(
            publisher_ip=STATIC_IP_ADDRESSES.VICON_IP, topic_filter="fz_right", timeout_ms=5
        )
        self.sub_bertec_left = Subscriber(
            publisher_ip=STATIC_IP_ADDRESSES.VICON_IP, topic_filter="fz_left", timeout_ms=5
        )

        self.bertec_estimator_left = BertecEstimator(
            self.sub_bertec_left, filter_size=self.filter_size
        )
        self.bertec_estimator_right = BertecEstimator(
            self.sub_bertec_right, filter_size=self.filter_size
        )

        # Period Tracker
        self.period_tracker = MovingAverageFilter(size=500)
        self.prev_end_time = TIME_METHOD()

        # Soft real time loop
        self.softRTloop = FlexibleSleeper(period=1 / EXO_THREAD_FREQUENCIES.BERTEC_FREQ)

    def pre_iterate(self, pause_event):
        """
        Sensor and Bertec reading
        Runs even if threads are paused
        """
        # Set starting time stamp
        self.data_dict["pitime"] = TIME_METHOD() - self.startstamp

        # Datetime time stamp
        self.data_dict['date_time'] = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMAT)

        new_stride_flag_left, force_left = self.bertec_estimator_left.update()
        new_stride_flag_right, force_right = self.bertec_estimator_right.update()

        # Add forces to data dict
        self.data_dict["forceplate_left"] = force_left
        self.data_dict["forceplate_right"] = force_right

        return new_stride_flag_left, new_stride_flag_right

    def iterate(self, new_stride_flag_left, new_stride_flag_right):
        """
        Update device estimates
        Does not run when threads paused
        """
        # Update exoboot threads if new state estimate
        if new_stride_flag_left:
            HS_l, stride_period_l, in_swing_l = (
                self.bertec_estimator_left.return_estimate()
            )

            # lag units reported in seconds
            lag_left = HS_l - self.device_thread_left.HS_imu

            self.device_thread_left.set_state_estimate(
                HS_l, stride_period_l, self.peak_torque_left, in_swing_l, lag_left
            )

        if new_stride_flag_right:
            HS_r, stride_period_r, in_swing_r = (
                self.bertec_estimator_right.return_estimate()
            )

            lag_right = HS_r - self.device_thread_right.HS_imu

            self.device_thread_right.set_state_estimate(
                HS_r, stride_period_r, self.peak_torque_right, in_swing_r, lag_right
            )

    def post_iterate(self):
        """
        Loop period tracking and soft real time pause
        """
        # Update Period Tracker
        end_time = TIME_METHOD()
        self.period_tracker.update(end_time - self.prev_end_time)
        self.prev_end_time = end_time
        my_freq = 1 / self.period_tracker.average()

        # Log gse freq
        self.data_dict["thread_freq"] = my_freq
        if self.loggingnexus and self.log_event.is_set():
            self.loggingnexus.append(self.name, copy.deepcopy(self.data_dict))

        # soft real-time loop
        self.softRTloop.pause()

    def run(self):
        """
        Custom run to continue catching heelstrike but not update estimates
        """
        self.on_pre_run()
        try:
            # print("GSE QUIT: ", self.quit_event.is_set())
            while self.quit_event.is_set():
                # print("GSE RUNNING")
                nslf, nsfr = self.pre_iterate(self.pause_event)
                if self.pause_event.is_set():
                    self.iterate(nslf, nsfr)
                else:
                    pass
                # print("GSE EXIT")
                self.post_iterate()
        except Exception as e:
            print("ERROR {}: {}".format(self.name, e))
        finally:
            pass
