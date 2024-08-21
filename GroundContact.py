import time
import numpy as np
from utils import MovingAverageFilterPlus

# class to determine ground contact 
hs_threshold = 50
to_threshold = 20

# class GroundContact: 
#     def __init__(self):
#         self.contact = False
#         self.TO_time = time.time()
#         self.HS_time = time.time()
#         self.time_in_current_stance = 0

#         self.stride_period_prev = 1.0 # Reasonable initial value
        
#         self.stride_period_filter = MovingAverageFilterPlus(cold_start=True, size=10)
#         self.stance_period_filter = MovingAverageFilterPlus(cold_start=True, size=10)
    
#     def update(self, force):
#         newContact = self.contact
#         if self.contact: # if no state change, i.e. we are in contact 
#             # compute current time in stance
#             self.time_in_current_stance = time.time() - self.HS_time 
            
#             if force < to_threshold: #there is no contact if the force is less than 20 N 
#                 newContact = False  
#         else:
#             if force >= hs_threshold: #there is a heel strike if force is greater than 50 N 
#                 newContact = True            
        
#         # if newContact has changed to true, means heel-strike, otherwise toe-off
#         if newContact != self.contact:  # Detects a state change
#             if newContact == True: # in this case we have a heel strike 
#                 stride_period_bertec = time.time() - self.HS_time
                
#                 stride_average_prev = self.stride_period_filter.trimmed_average()

#                 # Add all periods if filter is cold (empty)
#                 if not self.stride_period_filter.iswarm():
#                     self.stride_period_filter.update(stride_period_bertec)

#                 # Don't add period greater than +/-50% of previous stride period:
#                 elif abs(stride_period_bertec - stride_average_prev) / stride_average_prev > 0.5:
#                     self.stride_period_filter.update(stride_period_bertec)
                
#                 self.HS_time = time.time()
                
#             else: # in this case we have a toe off, so compute stance time
#                 self.TO_time = time.time()

#                 stance_period = self.TO_time - self.HS_time
                
#                 stance_average_prev = self.stance_period_filter.trimmed_average()

#                 # Add all periods if filter is cold (empty)
#                 if not self.stance_period_filter.iswarm():
#                     self.stride_period_filter.update(stance_period)
                
#                 # Don't add period greater than +/-50% of previous stride period:
#                 elif abs(stance_period - stance_average_prev) / stance_average_prev > 0.5:
#                     self.stance_period_filter.update(stance_period)
        
#         self.contact = newContact   # reset gait state to current gait state
        
#         return self.stance_period_filter.trimmed_average(), newContact, self.time_in_current_stance, self.stride_period_filter.trimmed_average()

import time
import numpy as np

# class to determine ground contact 
hs_threshold = 50
to_threshold = 20

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
            
            if force < to_threshold: #there is no contact if the force is less than 20 N 
                newContact = False  
        else:
            if force >= hs_threshold: #there is a heel strike if force is greater than 50 N 
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