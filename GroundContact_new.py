import time
import numpy as np

from config import HS_THRESHOLD, TO_THRESHOLD
from utils import MovingAverageFilterPlus

class GroundContact: 
    def __init__(self):
        self.inStance = False
        self.TO_time = time.time()
        self.HS_time = time.time()
        self.time_in_stride = 0

        # Track stride/stance periods
        self.stance_period_filter = MovingAverageFilterPlus(cold_start=True, size=10)  # cold_start=True start with empty buffer
        self.stride_period_filter = MovingAverageFilterPlus(cold_start=True, size=10)
    
    def update(self, force):
        # Swing to stance transisition
        if force > HS_THRESHOLD and not self.inStance:
            new_HS_time = time.time()
            self.time_in_stride = 0
            self.inStance = True

            self.HS_time = new_HS_time

            stride_period = self.TO_time - self.HS_time
            prev_stride_average = self.stride_period_filter.trimmed_average() # Historical estimate

            # Add all periods if filter is cold (empty)
            if not self.stride_period_filter.iswarm():
                self.stride_period_filter.update(stride_period)

            # Don't add period greater than +/-50% of previous stride period:
            elif abs(stride_period - prev_stride_average) / prev_stride_average > 1.0:
                self.stride_period_filter.update(stride_period)

            self.HS_time = new_HS_time

        # In stance
        elif force > HS_THRESHOLD and self.inStance:
            self.time_in_stride = time.time() - self.HS_time

        # Stance to swing transition
        elif force < TO_THRESHOLD and self.inStance:
            self.TO_time = time.time()
            self.time_in_stride = -1.0
            self.inStance = False

            stance_period = self.TO_time - self.HS_time
            prev_stance_average = self.stance_period_filter.trimmed_average() # Historical estimate

            # Add all periods if filter is cold (empty)
            if not self.stride_period_filter.iswarm():
                self.stride_period_filter.update(stance_period)

            # Don't add period greater than +/-50% of previous stride period:
            elif abs(stance_period - prev_stance_average) / prev_stance_average > 1.0:
                self.stance_period_filter.update(stance_period)

        # In swing
        else:
            self.time_in_stride = -1.0

        return self.stance_period_filter.trimmed_average(), self.inStance, self.time_in_stride, self.stride_period_filter.trimmed_average()


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
