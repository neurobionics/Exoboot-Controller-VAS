# Description: 
# This class generates a torque using Collin & Zhang's four point spline method
#
# Author: Nundini Rawal
# Date: 06/14/2024

import numpy as np
from scipy.interpolate import CubicSpline
import config

class FourPointSpline:
    def __init__(self, exo, t_rise:float=30, t_peak:float=50, t_fall:float=15, t_toe_off:float=65, holding_torque_threshold:float=2):
        # fixed high-level-control parameters for uphill walking
        self.exo = exo
        self.t_rise = t_rise        # % stance from t_peak
        self.t_peak = t_peak	    # % stance from heel strike
        self.t_fall = t_fall        # % stance from t_peak
        self.t_toe_off = t_toe_off  # % stance from heel strike
        self.holding_torque = holding_torque_threshold
        
        # self.start_rising_spline_flag_left = False
        # self.start_rising_spline_flag_right = False
        # self.t_onset_vec_left = []
        # self.t_onset_vec_right = []
        
        # self.cross_zero_time_left = 0
        # self.cross_zero_time_right = 0
        
    def current_generator_MAIN(self, time_in_current_stride:float, stride_period:float, peak_current:float)->float:
        """Generate current curve based on peak current etc.
        args:
            time_in_current_stride: time in current stride in seconds
            stride_period: average stride period
            peak_current: peak torque commanded by user via GUI
        
        returns:
            desired current: current value at current time in stride
        """
        
        time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        stride_t_onset = time_nodes[0]
        stride_t_dropoff = time_nodes[1]
        stride_t_toe_off = time_nodes[2]
        stride_t_peak = time_nodes[3] 
        
        if config.in_swing:
            output_current = self.exo.bias_current
        else:
            # Send current
            if (time_in_current_stride > 0) and (time_in_current_stride <= stride_t_onset):
                output_current = self.exo.bias_current

            elif (time_in_current_stride > stride_t_onset) and (time_in_current_stride <= stride_t_peak):
                currents = [self.exo.bias_current, peak_current]
                t_nodes = [stride_t_onset, stride_t_peak]
                
                # Rising spline until peak time
                rising_spline = CubicSpline(t_nodes, currents,bc_type='clamped')  
                output_current = rising_spline(time_in_current_stride)

            elif (time_in_current_stride > stride_t_peak) and (time_in_current_stride <= stride_t_dropoff):
                currents = [peak_current, self.exo.bias_current]
                t_nodes = [stride_t_peak, stride_t_dropoff]
                
                # Falling spline until offset time
                falling_spline = CubicSpline(t_nodes, currents,bc_type='clamped')
                output_current =  falling_spline(time_in_current_stride)      
                
                self.y_intercept = output_current
                self.previous_time = time_in_current_stride
                
            elif (time_in_current_stride > stride_t_dropoff) and (time_in_current_stride <= stride_t_toe_off):
                # linear ramp down to bias current of 1A until toe-off time
                output_current = (((self.exo.bias_current - self.y_intercept) / (stride_t_toe_off - stride_t_dropoff) )*(time_in_current_stride - self.previous_time)) + self.y_intercept 
            else:
                # either less than 0% or greater than toe-off (in Swing)
                output_current = self.exo.bias_current

        return output_current
        
    def current_generator_test(self, side, time_in_current_stride:float, stride_period:float, peak_current:float)->float:
        """Generate current curve based on peak current etc.
        args:
            time_in_current_stride: time in current stride in seconds
            stride_period: average stride period
            peak_current: peak torque commanded by user via GUI
        
        returns:
            desired current: current value at current time in stride
        """
        
        time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        
        # Depending on side, determine onset time shift and the onset time itself
        if side == "left":
            onset_shift = time_nodes[0] - self.cross_zero_time_left #-14 shift here ???
            print("Left shift",onset_shift)
            stride_t_onset = self.cross_zero_time_left
            print("Onset time Left",stride_t_onset)
        elif side == "right":
            onset_shift = time_nodes[0] - self.cross_zero_time_right
            print("Right shift",onset_shift)
            stride_t_onset = self.cross_zero_time_right
            print("Onset time Right",stride_t_onset)    #  0?? Not changing
        else:
            print("error: current_generator_test")
            
        # apply the shift to the other parameters
        stride_t_onset = time_nodes[0]
        stride_t_dropoff = time_nodes[1]
        stride_t_toe_off = time_nodes[2]
        stride_t_peak = time_nodes[3]
        
        # depending on side, if the rising hasn't started, check if curr ank angle < zero offset (more dorsi),
        # append to tonset vec and take the mean of last 5 str
        # Update t_onset and set cross_zero_time
        if side == "left" and config.ankle_angle_left < config.ankle_offset_left and self.start_rising_spline_flag_left == False:
            self.start_rising_spline_flag_left = True
            # determine time in current stride at which t_onset is occuring
            self.t_onset_vec_left.append(time_in_current_stride)
            self.cross_zero_time_left = np.mean(self.t_onset_vec_left[-5:])
        elif side == "right" and config.ankle_angle_right < config.ankle_offset_right and self.start_rising_spline_flag_right == False:
            self.start_rising_spline_flag_right = True
            # determine time in current stride at which t_onset is occuring
            self.t_onset_vec_right.append(time_in_current_stride)
            self.cross_zero_time_right = np.mean(self.t_onset_vec_right[-5:])
                
        # if self.start_rising_spline_flag_right or self.start_rising_spline_flag_left:
        #     if (time_in_current_stride > stride_t_onset) and (time_in_current_stride <= stride_t_peak):
        #         currents = [1000, peak_current]
        #         t_nodes = [stride_t_onset, stride_t_peak]
                
        #         # spline until peak time
        #         rising_spline = CubicSpline(t_nodes, currents,bc_type='clamped')  
        #         output_current =  rising_spline(time_in_current_stride)
        #         # print('Rising to Peak Torque')  
        
        # Send torques
        if (time_in_current_stride > 0) and (time_in_current_stride <= stride_t_onset):
            # linear ramp from 0 to holding torque
            # output_torque = ( (self.holding_torque - 0) /(stride_t_onset - 0)) * time_in_current_stride 
            output_current = 1000       

        elif (time_in_current_stride > stride_t_onset) and (time_in_current_stride <= stride_t_peak):
                currents = [1000, peak_current]
                t_nodes = [stride_t_onset, stride_t_peak]
                
                # spline until peak time
                rising_spline = CubicSpline(t_nodes, currents,bc_type='clamped')  
                output_current =  rising_spline(time_in_current_stride)

        elif (time_in_current_stride > stride_t_peak) and (time_in_current_stride <= stride_t_dropoff):
            currents = [peak_current, 1000]
            t_nodes = [stride_t_peak, stride_t_dropoff]
            
            # spline until offset time
            falling_spline = CubicSpline(t_nodes, currents,bc_type='clamped')
            output_current =  falling_spline(time_in_current_stride)      
            
            self.y_intercept = output_current
            self.previous_time = time_in_current_stride
            # print('Falling from Peak Torque')  
        elif (time_in_current_stride > stride_t_dropoff) and (time_in_current_stride <= stride_t_toe_off):
            # linear until toe-off time
            output_current = (((1000 - self.y_intercept) / (stride_t_toe_off - stride_t_dropoff) )*(time_in_current_stride - self.previous_time)) + self.y_intercept 
        else:
            # either less than 0% or greater than toe-off (in Swing)
            output_current = 1000
            start_rising_spline_flag_left = False
            start_rising_spline_flag_right = False

        return output_current

    def torque_generator_MAIN(self, time_in_current_stride:float, stride_period:float, peak_torque:float, in_swing_flag:bool)->float: # in_swing:bool
        """Generate torque curve based on current time in stride.
        args:
            time_in_current_stride: time in current stride
            stride_period: average stride period
            peak_torque: peak torque commanded by user via GUI
        
        returns:
            torque: torque value at current time in stride
        """

        time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        stride_t_onset = time_nodes[0]
        stride_t_dropoff = time_nodes[1]
        stride_t_toe_off = time_nodes[2]
        stride_t_peak = time_nodes[3]
               
        if in_swing_flag:
            output_torque = self.holding_torque
        else:
            if (time_in_current_stride > 0) and (time_in_current_stride <= stride_t_onset):
                # linear ramp from 0 to holding torque ~ output_torque = ( (self.holding_torque - 0) /(stride_t_onset - 0)) * time_in_current_stride 
                output_torque = self.holding_torque 
                
            elif (time_in_current_stride > stride_t_onset) and (time_in_current_stride <= stride_t_peak):
                torques = [self.holding_torque, float(peak_torque)]
                t_nodes = [stride_t_onset, stride_t_peak]
                
                # Rising spline until peak time
                rising_spline = CubicSpline(t_nodes, torques,bc_type='clamped')  
                output_torque =  rising_spline(time_in_current_stride)    

            elif (time_in_current_stride > stride_t_peak) and (time_in_current_stride <= stride_t_dropoff):
                torques = [float(peak_torque), self.holding_torque]
                t_nodes = [stride_t_peak, stride_t_dropoff]
                
                # Falling spline until offset time
                falling_spline = CubicSpline(t_nodes, torques,bc_type='clamped')
                output_torque =  falling_spline(time_in_current_stride)      
                
                # self.y_intercept = output_torque 
                # self.previous_time = time_in_current_stride
            elif (time_in_current_stride > stride_t_dropoff) and (time_in_current_stride <= stride_t_toe_off):
                # linear fall to bias current until toe-off time
                output_torque = self.holding_torque #(((self.holding_torque - self.y_intercept) / (stride_t_toe_off - stride_t_dropoff) )*(time_in_current_stride - self.previous_time)) + self.y_intercept 
            else:
                # either less than 0% or greater than toe-off (including swing if misclassified)
                output_torque = self.holding_torque
            
        return output_torque
    
    def torque_generator_stance_MAIN(self, time_in_current_stance:float, stride_period:float, stance_period:float, peak_torque:float, in_swing_flag:bool)->float:
        """Generate torque curve based on current time in stance. Torque is held at holding torque when in_swing_flag is tripped, otherwise
        exo actuates according to thresholds set in terms of stance phase.
        
        args:
            time_in_current_stance: time in current stance
            stance_period: average stance period
            peak_torque: peak torque commanded by user via GUI
            in_swing_flag: boolean flag for swing phase
        
        returns:
            torque: torque value at current time in stride
        """
        
        time_nodes = self.convert_percent_stride_thresholds_to_stance_times(stride_period, stance_period)
        stance_t_onset = time_nodes[0]
        stance_t_dropoff = time_nodes[1]
        stance_t_peak = time_nodes[2]
               
        if (in_swing_flag):
            output_torque = self.holding_torque 
        else:
            if (time_in_current_stance > 0) and (time_in_current_stance <= stance_t_onset):
                # linear ramp from 0 to holding torque ~ output_torque = ( (self.holding_torque - 0) /(stance_t_onset - 0)) * time_in_current_stance 
                output_torque = self.holding_torque
                
            elif (time_in_current_stance > stance_t_onset) and (time_in_current_stance <= stance_t_peak):
                torques = [self.holding_torque, float(peak_torque)]
                t_nodes = [stance_t_onset, stance_t_peak]
                
                # Rising spline until peak time
                rising_spline = CubicSpline(t_nodes, torques,bc_type='clamped')  
                output_torque =  rising_spline(time_in_current_stance)    

            elif (time_in_current_stance > stance_t_peak) and (time_in_current_stance <= stance_t_dropoff):
                torques = [float(peak_torque), self.holding_torque]
                t_nodes = [stance_t_peak, stance_t_dropoff]
                
                # Falling spline until offset time
                falling_spline = CubicSpline(t_nodes, torques,bc_type='clamped')
                output_torque =  falling_spline(time_in_current_stance)      
                
            else:
                # either less than 0% or greater than toe-off (including swing if misclassified)
                output_torque = self.holding_torque
            
        return output_torque
    
    def convert_percent_stride_thresholds_to_stance_times(self, stride_period:float, stance_period:float)->list:
            """Converts thresholds from units of % stride to seconds within the current stance phase
            using the average stance period

            args:
                None
            
            returns:
                stance_t_peak: time of peak torque in current stance
                stance_t_toe_off: time of toe off in current stance
                stance_t_onset: time of torque onset in current stance
                stance_t_dropoff: time of torque dropoff in current stance
            """
            # scale the thresholds from in terms of % stride to % stance:
            stance_t_peak = (self.t_peak / 100) * (stride_period / stance_period)
            stance_t_rise = (self.t_rise / 100) * (stride_period / stance_period)
            stance_t_fall = (self.t_fall / 100) * (stride_period / stance_period)
            
            # calculate time of torque onset and dropoff
            stance_t_onset = stance_t_peak - stance_t_rise
            stance_t_dropoff = stance_t_peak + stance_t_fall

            return [stance_t_onset, stance_t_dropoff, stance_t_peak]

    def convert_percent_thresholds_to_time(self, stride_period:float)->list:
            """Converts thresholds from units of % stride to seconds within the current 
            stride using the average stride period

            args:
                None
            
            returns:
                stride_t_peak: time of peak torque in current stride
                stride_t_toe_off: time of toe off in current stride
                t_onset: time of torque onset in current stride
                t_dropoff: time of torque dropoff in current stride
            """
            stride_t_peak = self.t_peak / 100 * stride_period
            stride_t_rise = self.t_rise / 100 * stride_period
            stride_t_fall = self.t_fall / 100 * stride_period
            stride_t_toe_off = self.t_toe_off / 100 * stride_period

            # calculate time of torque onset and dropoff
            stride_t_onset = stride_t_peak - stride_t_rise
            stride_t_dropoff = stride_t_peak + stride_t_fall

            return [stride_t_onset, stride_t_dropoff, stride_t_toe_off, stride_t_peak]