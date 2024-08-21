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
