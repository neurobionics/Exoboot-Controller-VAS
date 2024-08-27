# Description: 
# A class for implementing a software real-time loop.
#
# Original Author: Varun Satyadev Shetty
# Date: 06/17/2024


import sys
import os
import time

class DelayTimer():
    def __init__(self, delay_time, true_until: bool = False):
        '''
        A timer

        Args:
            delay_time: amount of time to delay (s)
            true_until: option to make the timer go True until delay_time is reached, then False
        '''
        self.delay_time = delay_time
        self.true_until = true_until
        self.start_time = None  # Means timer is "inactive"

    def start(self):
        '''Starts the timer.'''
        self.start_time = time.perf_counter()

    def check(self):
        '''Depending on true_until, will either go True when time is hit, or go False when time is hit.'''
        if self.true_until:
            if self.start_time is not None and time.perf_counter() < self.start_time + self.delay_time:
                return True
            else:
                return False
        else:
            if self.start_time is not None and time.perf_counter() > self.start_time + self.delay_time:
                return True
            else:
                return False

    def reset(self):
        self.start_time = None

    def get_time(self):
        return time.perf_counter() - self.start_time



class FlexibleTimer():
    '''A timer that attempts to reach consistent desired freq by variable pausing.'''

    def __init__(self, target_freq):
        self.target_period = 1/target_freq
        self.last_time = time.perf_counter()
        self.over_time = 0
        self.warning_timer = DelayTimer(delay_time=3)
        self.do_count_errors = True

    def pause(self):
        '''main function for keeping timer constant.'''
        if self.do_count_errors:
            if time.perf_counter()-self.last_time > self.target_period:
                # Penalty for cycle going over time
                self.over_time += 1
            else:
                # liberal reset for every good period
                self.over_time = max(0, self.over_time - 5)
                # Throw warning if target freqeuncy is not being hit
            if self.over_time > 30:
                self.warning_timer.start()
                self.do_count_errors = False  # Stop counting errors for now

        # Use timer to prevent excessive warnings.
        else:
            if self.warning_timer.check():
                print('Warning: Target Frequency is not being hit!')
                self.over_time = 0  # reset over_time counter
                self.warning_timer.reset()  # reset warning timer
                self.do_count_errors = True

        # Main logic
        while time.perf_counter()-self.last_time < self.target_period:
            pass
        self.last_time = time.perf_counter()

class FlexibleSleeper():
    """
    Inactive timer using sleep by delay
    """
    def __init__(self, period):
        self.period = period
        self.last_stop_time = time.perf_counter()

    def pause(self):
        current_time = time.perf_counter()
        delay = max(self.period - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        self.last_stop_time = self.stop_time

    def pause_return(self):
        current_time = time.perf_counter()
        delay = max(self.period - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        period = self.stop_time - self.last_stop_time 
        self.last_stop_time = self.stop_time
        return period
