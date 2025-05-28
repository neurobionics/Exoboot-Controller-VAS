# Description: 
# AssistanceGenerator creates a generic 4 point spline profile based on 4 parameters:
# rise time, peak torque time, fall time, and toe-off time.
#
# Profile is linearly scaled to fit profile to given max torque
#
# Profile saved as dict for fast lookup in terms of % stride
#
# Author: Nundini Rawal, John Hutchinson
# Date: 06/14/2024

from scipy.interpolate import CubicSpline
from opensourceleg.utilities import SoftRealtimeLoop

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.gse_utils import WalkingSimulator
from settings.constants import(
    INCLINE_WALK_TIMINGS, 
    BIAS_CURRENT,
    HOLDING_TORQUE)

class AssistanceGenerator:
    def __init__(self, 
                 p_rise:float=INCLINE_WALK_TIMINGS.P_RISE, 
                 p_peak:float=INCLINE_WALK_TIMINGS.P_PEAK, 
                 p_fall:float=INCLINE_WALK_TIMINGS.P_FALL, 
                 p_toe_off:float=INCLINE_WALK_TIMINGS.P_TOE_OFF, 
                 holding_torque:float=HOLDING_TORQUE, 
                 bias_current:int=BIAS_CURRENT)->None:
        
        self.p_rise = p_rise        # % stance from p_peak
        self.p_peak = p_peak	    # % stance from heel strike
        self.p_fall = p_fall        # % stance from p_peak
        self.p_toe_off = p_toe_off  # % stance from heel strike
        
        self.end_of_stride_in_percent = 100

        self.holding_torque = holding_torque
        self.bias_current = bias_current

    def set_new_timing_params(self, p_rise:float, p_peak:float, p_fall:float, p_toe_off:float)->None:
        """
        Use to set new timing parameters.
        All arguments required.
        """
        try:
            self.p_rise = p_rise
            self.p_peak = p_peak
            self.p_fall = p_fall
            self.p_toe_off = p_toe_off
        except:
            raise Exception("set_new_timing_params failed in assistance generator")

    def set_holding_params(self, holding_torque:float, bias_current:float)->None:
        """
        Use to set a new holding torque or bias current
        
        Args:
            holding_torque: in Nm
            bias_current: in mA
        """
        self.holding_torque = holding_torque
        self.bias_current = bias_current
    
    def set_my_generic_profile(self, granularity:int=10000)->None:
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
        p_peak = self.p_peak / self.end_of_stride_in_percent
        p_rise = self.p_rise / self.end_of_stride_in_percent
        p_fall = self.p_fall / self.end_of_stride_in_percent
        # p_toe_off = self.p_toe_off / self.end_of_stride_in_percent

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

    def scale_torque(self, torque:float, min_new:float, max_new:float)-> float:
        """
        Linearly scales torque from [generic_min, generic_max] to [min_new, max_new]
        """
        return (max_new - min_new) / (self.generic_max - self.generic_min) * (torque - self.generic_min) + min_new

    def get_generic_torque_command(self, percent_stride:float)->float:
        """
        Evaluate generic_profile at percent_stride

        convert percent_stride nearest integer index

        less error from int casting by increasing granularity
        """
        generic_index = min(int(percent_stride * self.granularity), self.granularity - 1)
        
        return self.generic_profile[generic_index]

    def generic_torque_generator(self, current_time:float, stride_period:float, peak_torque:float, in_swing:bool)->float:
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
    
    # instantiate assistance generator
    assistance_generator = AssistanceGenerator()
    
    # load profile timings and create generic profile
    assistance_generator.set_my_generic_profile(granularity=10000)
    
    # instantiate the walking simulator
    walker = WalkingSimulator(stride_period=1.2)
    walker.set_percent_toe_off(percent_toe_off=INCLINE_WALK_TIMINGS.P_TOE_OFF)
    
    # instantiate the osl's softrt loop
    clock = SoftRealtimeLoop(dt=1/1)
    
    # create a set of peak torques to test
    peak_torques = [0, 7, 15, 27, 35, 40]
    
    for t in clock:
        if t <= 2:
            peak_torque = peak_torques[0]
        elif t > 2 and t <= 4:
            peak_torque = peak_torques[1]
        elif t > 4 and t <= 6:
            peak_torque = peak_torques[2]
        elif t > 6 and t <= 8:
            peak_torque = peak_torques[3]
        elif t > 18 and t <= 10:
            peak_torque = peak_torques[4]
        elif t > 10 and t <= 12:
            peak_torque = peak_torques[5]
            
            
        # acquire torque command based on gait estimate
        torque_command = assistance_generator.generic_torque_generator(t, walker.stride_period, peak_torque, walker.in_swing_flag)