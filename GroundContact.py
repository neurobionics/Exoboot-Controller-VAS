import time
import numpy as np
from utils import MovingAverageFilter
from constants import HS_THRESHOLD, TO_THRESHOLD, ACCEPT_STRIDE_THRESHOLD, ACCEPT_STANCE_THRESHOLD

class GroundContact: 
    def __init__(self):
        self.contact = False
        self.TO_time = time.time()
        self.HS_time = time.time()
        
        self.movmean_window_sz = 10
        self.stance_period = 0.92   # initial guess of stance time (@ 0.8m/s & 1.0)
        self.stride_period_bertec = 1.2 # initial guess of stride time (@ 0.8m/s & 1.0)
        self.time_diffs = [self.stance_period] * (self.movmean_window_sz-1)
        self.stride_periods = [self.stride_period_bertec] * (self.movmean_window_sz-1)   

        self.time_in_current_stance = 0
    
    def update(self, force):
        newContact = self.contact
        if self.contact: # if no state change, i.e. we are in contact 
            # compute current time in stance
            self.time_in_current_stance = time.time() - self.HS_time 
            
            if force < TO_THRESHOLD: #there is no contact if the force is less than 20 N 
                newContact = False  
        else:
            if force >= HS_THRESHOLD: #there is a heel strike if force is greater than 50 N 
                newContact = True            
        
        # if newContact has changed to true, means heel-strike, otherwise toe-off
        if newContact != self.contact:  # Detects a state change
            if newContact == True: # in this case we have a heel strike 
                temp_stride_period_bertec = time.time() - self.HS_time
                
                # make sure stride_period is appropriate before appending to averaging list:
                if((0.8*self.stride_period_bertec) <= temp_stride_period_bertec <= (1.20*self.stride_period_bertec)):
                    self.stride_periods.append(temp_stride_period_bertec)
                
                # Moving average window:
                if len(self.stride_periods) > self.movmean_window_sz:
                    self.stride_periods.pop(0) 
    
                if len(self.stride_periods) >= self.movmean_window_sz:
                    self.stride_period_bertec = np.mean(self.stride_periods)
                    
                self.HS_time = time.time()
                
            else: # in this case we have a toe off, so compute stance time
                self.TO_time = time.time()
                time_diff = self.TO_time - self.HS_time
                
                # make sure stance period is appropriate before appending to averaging list:
                if((0.8*self.stance_period) <= time_diff <= (1.20*self.stance_period)):
                    self.time_diffs.append(time_diff)

                # Moving average window:
                if len(self.time_diffs) > self.movmean_window_sz:
                    self.time_diffs.pop(0) 
    
                if len(self.time_diffs) >= self.movmean_window_sz:
                    self.stance_period = np.mean(self.time_diffs)
        
        self.contact = newContact   # reset gait state to current gait state
                
        return self.stance_period, newContact, self.time_in_current_stance, self.stride_period_bertec


class BertecEstimator:
    """
    New Class for Bertec estimation

    returns left/right estimate: HS, stride/stance period, and in_swing (not in contact)

    get_estimate returns new stride flags which only update if new estimate has occurred
    """
    def __init__(self, subscriber_left, subscriber_right, filter_size=10):
        # ZMQ Subscriber
        self.subscriber_left = subscriber_left
        self.subscriber_right = subscriber_right

        self.HS_left = time.perf_counter()
        self.HS_right = time.perf_counter()
        self.TO_left = time.perf_counter()
        self.TO_right = time.perf_counter()

        self.prev_fp_l = 0
        self.prev_fp_r = 0

        # Phase in gait: True is stance
        self.contact_left = False
        self.contact_right = False

        # Moving average filter for stride period
        stride_period_init = 1.2 # initial guess of stride time (@ 0.8m/s & 1.0)
        stance_period_init = 0.92   # initial guess of stance time (@ 0.8m/s & 1.0)

        # Track stride/stance periods
        self.stride_period_filter_l = MovingAverageFilter(initial_value=stride_period_init, size=filter_size) # cold_start=True start with empty buffer
        self.stride_period_filter_r = MovingAverageFilter(initial_value=stride_period_init, size=filter_size)
        self.stance_period_filter_l = MovingAverageFilter(initial_value=stance_period_init, size=filter_size) # cold_start=True start with empty buffer
        self.stance_period_filter_r = MovingAverageFilter(initial_value=stance_period_init, size=filter_size)

    def return_estimate_left(self):
        return self.HS_left, self.stride_period_filter_l.average(), not self.contact_left
    
    def return_estimate_right(self):
        return self.HS_right, self.stride_period_filter_r.average(), not self.contact_right

    def get_estimate(self, pause_event):
        """
        Using Bertec forceplate thresholding to determine HS/TO

        Only updates filters if threads are not paused
        """
        topic_left, fp_l, timestep_valid_left = self.subscriber_left.get_message()
        topic_right, fp_r, timestep_valid_right = self.subscriber_right.get_message()

        # Catch empty messages
        fp_l = self.prev_fp_l if (fp_l == '') else float(fp_l)
        fp_r = self.prev_fp_r if (fp_r == '') else float(fp_r)
        
        """Left Side"""
        new_stride_flag_left = False
        if self.contact_left:
            if fp_l < TO_THRESHOLD:
                in_contact_left = False # Leaving contact

                self.TO_left = time.perf_counter()
                new_stance_period_left = self.TO_left - self.HS_left
                stance_estimate_left = self.stance_period_filter_l.average()
                
                # New period is within +/-ACCEPT_STANCE_THRESHOLD of estimate and thread is not paused
                if abs((new_stance_period_left - stance_estimate_left) / stance_estimate_left) < ACCEPT_STANCE_THRESHOLD and pause_event.is_set():
                    self.stance_period_filter_l.update(new_stance_period_left)
            else:
                in_contact_left = True  # Still in contact
        else:
            if fp_l >= HS_THRESHOLD: #there is a heel strike if force is greater than 50 N 
                in_contact_left = True
                new_stride_flag_left = True

                new_HS_left = time.perf_counter()
                new_stride_period_left = new_HS_left - self.HS_left
                stride_period_estimate_left = self.stride_period_filter_r.average()

                # New period is within +/-ACCEPT_STRIDE_THRESHOLD of estimate and thread is not paused
                if abs((new_stride_period_left - stride_period_estimate_left) / stride_period_estimate_left) < ACCEPT_STRIDE_THRESHOLD and pause_event.is_set():
                    self.stride_period_filter_l.update(new_stride_period_left)
                    
                self.HS_left = new_HS_left
            else:
                in_contact_left = False        
        
        """Right Side"""
        new_stride_flag_right = False
        if self.contact_right:
            if fp_r < TO_THRESHOLD:
                in_contact_right = False # Leaving contact

                self.TO_right = time.perf_counter()
                new_stance_period_right = self.TO_right - self.HS_right
                stance_estimate_right = self.stance_period_filter_l.average()
                
                # make sure stance period is appropriate before appending to averaging list:
                if abs((new_stance_period_right - stance_estimate_right) / stance_estimate_right) < ACCEPT_STANCE_THRESHOLD and pause_event.is_set():
                    self.stance_period_filter_l.update(new_stance_period_right)
            else:
                in_contact_right = True  # Still in contact
        else:
            if fp_r >= HS_THRESHOLD: #there is a heel strike if force is greater than 50 N 
                in_contact_right = True
                new_stride_flag_right = True

                new_HS_right = time.perf_counter()
                new_stride_period_right = new_HS_right - self.HS_right
                stride_period_estimate_right = self.stride_period_filter_r.average()
                # make sure stride_period is appropriate before appending to averaging list:
                if abs((new_stride_period_right - stride_period_estimate_right) / stride_period_estimate_right) < ACCEPT_STRIDE_THRESHOLD and pause_event.is_set():
                    self.stride_period_filter_l.update(new_stride_period_right)
                    
                self.HS_right = new_HS_right
            else:
                in_contact_right = False
        
        # Update value histories
        self.contact_left = in_contact_left
        self.contact_right = in_contact_right
        self.prev_fp_l = fp_l
        self.prev_fp_r = fp_r

        return new_stride_flag_left, new_stride_flag_right, fp_l, fp_r
