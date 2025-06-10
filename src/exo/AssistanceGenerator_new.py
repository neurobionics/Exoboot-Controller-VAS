# Description: 
# AssistanceGenerator Creates generic 4 point spline profile based on 4 parameters
#
# Profile is linearly scaled to fit profile to given max torque
#
# Profile saved as dict for fast lookup in terms of % stride
#
# Author: Nundini Rawal, John Hutchinson
# Date: 06/14/2024

import numpy as np
from scipy.interpolate import CubicSpline
from constants import END_OF_STRIDE
from constants import P_RISE, P_PEAK, P_FALL, P_TOE_OFF, HOLDING_TORQUE, BIAS_CURRENT

class AssistanceGenerator:
    def __init__(self, p_rise:float=P_RISE, p_peak:float=P_PEAK, p_fall:float=P_FALL, p_toe_off:float=P_TOE_OFF, holding_torque:float=HOLDING_TORQUE, bias_current:int=BIAS_CURRENT):
        # fixed high-level-control parameters for uphill walking
        self.p_rise = p_rise        # % stance from p_peak
        self.p_peak = p_peak	    # % stance from heel strike
        self.p_fall = p_fall        # % stance from p_peak
        self.p_toe_off = p_toe_off  # % stance from heel strike

        self.holding_torque = holding_torque
        self.bias_current = bias_current

    def load_timings(self, timings_dict):
        """
        Set timings from dict

        Needs all entries to set succesfully
        """
        try:
            self.p_rise = timings_dict['P_RISE']
            self.p_peak = timings_dict['P_PEAK']
            self.p_fall = timings_dict['P_FALL']
            self.p_toe_off = timings_dict['P_TOE_OFF']
            self.holding_torque = timings_dict['HOLDING_TORQUE']
            self.bias_current = timings_dict['BIAS_CURRENT']
        except:
            raise Exception("set_timings failed in assistance generator; provided dict missing entries")

    def set_my_generic_profile(self, granularity=10000):
        """
        Creates generic cubic spline based profile using timing parameters
        percent range: [0, 1]
        torque range: [0, 1]

        sets generic_profile dictionary as attribute of class
        
        dictionary is size granularity indexed by ints from 0 to granularity

        NEED TO RUN BEFORE generic_torque_generator OTHERWISE NO PROFILE WILL EXIST
        """
        self.granularity = granularity

        # Torque range
        self.generic_min = 0
        self.generic_max = 1

        # Convert Nodes to % stride
        p_peak = self.p_peak / END_OF_STRIDE
        p_rise = self.p_rise / END_OF_STRIDE
        p_fall = self.p_fall / END_OF_STRIDE
        # p_toe_off = self.p_toe_off / END_OF_STRIDE

        # Calculate time of torque onset and dropoff
        p_onset = p_peak - p_rise
        p_dropoff = p_peak + p_fall

        # Spline sections
        rising_spline = CubicSpline([p_onset, p_peak], [self.generic_min, self.generic_max], bc_type='clamped')
        falling_spline = CubicSpline([p_peak, p_dropoff], [self.generic_max, self.generic_min],bc_type='clamped')

        generic_profile = {}
        for i in range(self.granularity):
            percent = i / self.granularity

            # Profile Conditions
            if (percent > 0) and (percent <= p_onset):
                # Onset
                output_torque = self.generic_min
            elif (percent > p_onset) and (percent <= p_peak):
                # Rising
                output_torque = rising_spline(percent)
            elif (percent > p_peak) and (percent <= p_dropoff):
                # Falling
                output_torque =  falling_spline(percent)
            else:
                output_torque = self.generic_min
        
            generic_profile[i] = output_torque

        self.generic_profile = generic_profile

    def scale_torque(self, torque, min_new, max_new):
        """
        Linearly scales torque from [generic_min, generic_max] to [min_new, max_new]
        """
        return (max_new - min_new) / (self.generic_max - self.generic_min) * (torque - self.generic_min) + min_new

    def get_generic_torque_command(self, percent_stride):
        """
        Evaluate generic_profile at percent_stride

        convert percent_stride nearest integer index

        less error from int casting by increasing granularity
        """
        generic_index = min(int(percent_stride * self.granularity), self.granularity - 1)
        return self.generic_profile[generic_index]

    def generic_torque_generator(self, current_time, stride_period, peak_torque, in_swing):
        """
        Calculates torque command from generic_profile

        Uses gait estimate (current_time, stride_period) and scales by peak_torque
        """
        if in_swing:
            torque_command = self.holding_torque
        else:
            # Convert time to percent stride
            percent_stride = current_time / stride_period

            # Get generic command
            generic_command = self.get_generic_torque_command(percent_stride)

            # Scale command using given peak torque
            torque_command = self.scale_torque(generic_command, self.holding_torque, peak_torque)

        return torque_command



if __name__ == "__main__":
    import numpy as np
    import time

    def scale_torque(torque, min_new, max_new, gen_min, gen_max):
        """
        Linearly scales torque from [generic_min, generic_max] to [min_new, max_new]
        """
        return (max_new - min_new) / (gen_max - gen_min) * (torque - gen_min) + min_new

    torque = 0.8
    min_new = 2
    max_new = 40 * np.random.random_sample()
    gen_min = 0.123
    gen_max = 0.999

    starttime = time.perf_counter()
    expl = scale_torque(torque, min_new, max_new, gen_min, gen_max)
    endtime = time.perf_counter()

    print(torque, min_new, max_new)
    print("expl: {}, {}", expl, endtime-starttime)

    starttime = time.perf_counter()
    input_torque_range = [gen_min, gen_max]
    output_torque_range = [min_new, max_new]
    npval = np.interp(torque, input_torque_range, output_torque_range)
    endtime = time.perf_counter()

    print("np: {}, {}", npval, endtime-starttime)
