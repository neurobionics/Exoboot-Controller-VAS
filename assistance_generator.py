# Description: 
# This class does mid-to-high level control by specifying the assistance of the exoskeleton via the following methods:
# 
# (1) Generates a current curve based on a peak commanded current and thresholds for the Four Point Spline method
#
# (2) Generates torque using Collin & Zhang's four point spline method. Takes in commanded GUI torque and in terms of % stride.
#
# (3) Generates torque using Collin & Zhang's four point spline method, BUT in terms of % stance phase rather than % stride as in (3)
#
# (4) Generates a biomimetic torque by scaling the biological ankle moment to the peak commanded torque
#
# Author: Nundini Rawal
# Date: 06/14/2024

import numpy as np
from scipy.interpolate import CubicSpline
import config
from config import END_OF_STANCE, END_OF_STRIDE
import csv

class AssistanceGenerator:
    def __init__(self, t_rise:float=30, t_peak:float=50, t_fall:float=15, t_toe_off:float=65, holding_torque_threshold:float=2, bias_current: float=750):
        # fixed high-level-control parameters for uphill walking
        self.t_rise = t_rise        # % stance from t_peak
        self.t_peak = t_peak	    # % stance from heel strike
        self.t_fall = t_fall        # % stance from t_peak
        self.t_toe_off = t_toe_off  # % stance from heel strike
        self.holding_torque = holding_torque_threshold
        self.bias_current = bias_current
        self.prev_commanded_rising = -1
        self.prev_commanded_falling = -1
        
        # Extract the biological ankle torque
        if config.in_torque_FSM_mode == False:
            traj_filename = "biol_ank_moment_traj.csv" 
            with open(traj_filename, mode='r') as csv_reader:
                csv_reader = csv.reader(csv_reader)
                biomimetic_torque_curve = list(csv_reader)
                self.biomimetic_torque_curve = np.array([float(i) for i in biomimetic_torque_curve[0]])

            # peak biological ankle torque to scale by in torque generator method
            self.peak_biol_ankle_moment = np.max(self.biomimetic_torque_curve)

            # specify the percent gait cycle for the biological ankle torque
            self.percentGait = np.linspace(0,1,len(self.biomimetic_torque_curve))
                
    def current_generator_MAIN(self, time_in_current_stride:float, stride_period:float, peak_current:float, in_swing_flag:bool)->float:
        """Generate current curve based on peak current etc.
        args:
            time_in_current_stride: time since last HS
            stride_period: average stride period
            peak_current: peak torque commanded by user via GUI
        
        returns:
            desired current: current value at current time in stride
        """
        
        time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        stride_t_onset = time_nodes[0]
        stride_t_peak = time_nodes[1]
        stride_t_dropoff = time_nodes[2]
        # stride_t_toe_off = time_nodes[3]
        
        if in_swing_flag:
            output_current = self.bias_current
        else:
            # Send current
            if (time_in_current_stride > 0) and (time_in_current_stride <= stride_t_onset):
                output_current = self.bias_current

            elif (time_in_current_stride > stride_t_onset) and (time_in_current_stride <= stride_t_peak):
                currents = [self.bias_current, peak_current]
                t_nodes = [stride_t_onset, stride_t_peak]
                
                # Rising spline until peak time
                rising_spline = CubicSpline(t_nodes, currents,bc_type='clamped')  
                output_current = rising_spline(time_in_current_stride)

            elif (time_in_current_stride > stride_t_peak) and (time_in_current_stride <= stride_t_dropoff):
                currents = [peak_current, self.bias_current]
                t_nodes = [stride_t_peak, stride_t_dropoff]
                
                # Falling spline until offset time
                falling_spline = CubicSpline(t_nodes, currents,bc_type='clamped')
                output_current =  falling_spline(time_in_current_stride)      
                
                self.y_intercept = output_current
                self.previous_time = time_in_current_stride
            else:
                # either less than 0% or greater than toe-off (in Swing)
                output_current = self.bias_current

        return output_current   

    def current_generator_stance_MAIN(self, time_in_current_stance:float, stride_period:float=1.12, stance_period:float=0.65, peak_current:float=750, in_swing:bool=False)->float:
            """Generate current curve based on peak current etc. but using the bertec treadmill and stance period
            args:
                time_in_current_stride: time since last HS
                stride_period: average stride period
                peak_current: peak torque commanded by user via GUI
            
            returns:
                desired current: current value at current time in stride
            """

            time_nodes = self.convert_percent_stride_thresholds_to_stance_times(stance_period)       
            stance_t_onset = time_nodes[0]
            stance_t_peak = time_nodes[1]
            stance_t_dropoff = time_nodes[2]
            
            if peak_current < self.bias_current:
                peak_current = self.bias_current
                
            if (in_swing):
                output_current = self.bias_current
            else:
                if (time_in_current_stance > 0) and (time_in_current_stance <= stance_t_onset):
                    # linear ramp from 0 to holding torque ~ output_torque = ( (self.holding_torque - 0) /(stance_t_onset - 0)) * time_in_current_stance 
                    output_current = self.bias_current
                    
                elif (time_in_current_stance > stance_t_onset) and (time_in_current_stance <= stance_t_peak):
                    # Only regen spline object when torque is changed, otherwise just eval using same object
                    if self.prev_commanded_rising != peak_current:
                        currents = [self.bias_current, peak_current]
                        t_nodes = [stance_t_onset, stance_t_peak]

                        # Rising spline until peak time
                        self.rising_spline = CubicSpline(t_nodes, currents,bc_type='clamped')  
                        self.prev_commanded_rising = peak_current
                    
                    output_current = self.rising_spline(time_in_current_stance)

                elif (time_in_current_stance > stance_t_peak) and (time_in_current_stance <= stance_t_dropoff):
                    if self.prev_commanded_falling != peak_current:
                        currents = [peak_current, self.bias_current]
                        t_nodes = [stance_t_peak, stance_t_dropoff]
                        
                        # Falling spline until offset time
                        self.falling_spline = CubicSpline(t_nodes, currents,bc_type='clamped')
                        self.prev_commanded_falling = peak_current
                    
                    output_current = self.falling_spline(time_in_current_stance)
                else:
                    # either less than 0% or greater than toe-off (including swing if misclassified)
                    output_current = self.bias_current
                    
                # Catch any instances of output torque being less than holding torque as a safety
                # i.e. when GUI commanded torque is first '0'
                if output_current < self.bias_current:
                    output_current = self.bias_current
                
            return output_current

    def torque_generator_MAIN(self, time_in_current_stride:float, stride_period:float, peak_torque:float, in_swing_flag:bool)->float:
        """Generate torque curve based on current time in stride.
        args:
            time_in_current_stride: time since last HS
            stride_period: average stride period
            peak_torque: peak torque commanded by user via GUI
        
        returns:
            torque: torque value at current time in stride
        """

        time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        stride_t_onset = time_nodes[0]
        stride_t_peak = time_nodes[1]
        stride_t_dropoff = time_nodes[2]
        # stride_t_toe_off = time_nodes[3]
               
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
            else:
                # either less than 0% or greater than toe-off (including swing if misclassified)
                output_torque = self.holding_torque
            
        return output_torque
    
    def torque_generator_stance_MAIN(self, time_in_current_stance:float, stride_period:float=1.12, stance_period:float=0.65, peak_torque:float=2, in_swing:bool=False)->float:
        """Generate torque curve based on current time in stance. Torque is held at holding torque when in_swing_flag is tripped, otherwise
        exo actuates according to thresholds set in terms of stance phase.
        
        args:
            time_in_current_stance: time since last HS
            stance_period: average stance period
            peak_torque: peak torque commanded by user via GUI
            in_swing_flag: boolean flag for swing phase
        
        returns:
            torque: torque value at current time in stride
        """
        time_nodes = self.convert_percent_stride_thresholds_to_stance_times(stance_period)       
        stance_t_onset = time_nodes[0]
        stance_t_peak = time_nodes[1]
        stance_t_dropoff = time_nodes[2]
        
        if peak_torque < self.holding_torque:
            peak_torque = self.holding_torque
               
        if (in_swing):
            output_torque = self.holding_torque
        else:
            if (time_in_current_stance > 0) and (time_in_current_stance <= stance_t_onset):
                output_torque = self.holding_torque
                
            elif (time_in_current_stance > stance_t_onset) and (time_in_current_stance <= stance_t_peak):
                # Only regen spline object when torque is changed, otherwise just eval using same object
                # if self.prev_commanded_rising != peak_torque:
                torques = [self.holding_torque, float(peak_torque)]
                t_nodes = [stance_t_onset, stance_t_peak]
                    
                # Rising spline until peak time
                self.rising_spline = CubicSpline(t_nodes, torques,bc_type='clamped')   
                # self.prev_commanded_rising = peak_torque
                    
                output_torque =  self.rising_spline(time_in_current_stance) 

            elif (time_in_current_stance > stance_t_peak) and (time_in_current_stance <= stance_t_dropoff):
                # if self.prev_commanded_falling != peak_torque:
                torques = [float(peak_torque), self.holding_torque]
                t_nodes = [stance_t_peak, stance_t_dropoff]
                
                # Falling spline until offset time
                self.falling_spline = CubicSpline(t_nodes, torques,bc_type='clamped')
                # self.prev_commanded_falling = peak_torque
                
                output_torque =  self.falling_spline(time_in_current_stance)      
                
            else:
                # either less than 0% or greater than toe-off (including swing if misclassified)
                output_torque = self.holding_torque
                
            # Catch any instances of output torque being less than holding torque as a safety
            # i.e. when GUI commanded torque is first '0'
            if output_torque < self.holding_torque:
                output_torque = self.holding_torque
            
        return output_torque
    
    def biomimetic_torque_generator_MAIN(self, time_in_current_stride:float, stride_period:float, peak_torque:float, in_swing_flag:bool)->float:
        """Generate biomimetic torque for current % stride by scaling biological ankle moment. 
        Torque is held at holding torque when in_swing_flag is tripped, otherwise actuate according to scaled profile
        
        args:
            time_in_current_stride: time in current stride
            stride_period: average stride period
            peak_torque: peak torque commanded by user via GUI
            in_swing_flag: boolean flag for swing phase
            
        returns:
            output_torque: torque value at current time in stride"""
        
        if (in_swing_flag):
            output_torque = self.holding_torque
        else:
            # scale the biological ankle torque to the peak torque
            biomimetic_assistive_traj = self.biomimetic_torque_curve*(peak_torque/self.peak_biol_ankle_moment)
            
            # create cubic spline params to fit the scaled biological ankle torque
            cubicsplinegen = CubicSpline(self.percentGait, biomimetic_assistive_traj)
            
            # determine current % stride and feed into fitting spline
            curr_percent_stride = time_in_current_stride/stride_period
            output_torque = cubicsplinegen(curr_percent_stride)
        
        # Clip to holding torque/peak torque
        output_torque_clipped = np.clip(output_torque, self.holding_torque, peak_torque)

        return output_torque_clipped
    
    def torque_generator_spike(self, time_in_current_stance:float, stride_period:float=1.12, stance_period:float=0.65, peak_torque:float=2, in_swing:bool=False)->float:
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

        time_nodes = self.convert_percent_stride_thresholds_to_stance_times(stance_period)       
        # time_nodes = self.convert_percent_thresholds_to_time(stride_period)
        stance_t_onset = time_nodes[0]
        stance_t_peak = time_nodes[1]
        stance_t_dropoff = time_nodes[2]
        # stance_t_toeoff = time_nodes[3]
               
        if False: #(in_swing):
            output_torque = self.holding_torque
        else:
            if (time_in_current_stance > 0) and (time_in_current_stance <= stance_t_onset):
                output_torque = self.holding_torque
                
            elif (time_in_current_stance > stance_t_onset) and (time_in_current_stance <= stance_t_peak):
                output_torque = 1.0 * float(peak_torque)

            elif (time_in_current_stance > stance_t_peak) and (time_in_current_stance <= stance_t_dropoff):
                output_torque = 0.5 * float(peak_torque) 
                
            else:
                output_torque = self.holding_torque
            
        return output_torque
     
    def convert_percent_stride_thresholds_to_stance_times(self, stance_period:float)->list:
            """Converts 4ptSpline thresholds from units of % stride to seconds within the current stance phase
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
            stance_t_peak = self.t_peak / END_OF_STANCE * stance_period
            stance_t_rise = self.t_rise / END_OF_STANCE * stance_period
            stance_t_fall = self.t_fall  / END_OF_STANCE * stance_period
            stance_t_toeoff = self.t_toe_off / END_OF_STANCE * stance_period

            # calculate time of torque onset and dropoff
            stance_t_onset = stance_t_peak - stance_t_rise
            stance_t_dropoff = stance_t_peak + stance_t_fall

            return [stance_t_onset, stance_t_peak, stance_t_dropoff, stance_t_toeoff]

    def convert_percent_thresholds_to_time(self, stride_period:float)->list:
            """Converts 4ptSpline thresholds from units of % stride to seconds within the current 
            stride using the average stride period

            args:
                None
            
            returns:
                stride_t_peak: time of peak torque in current stride
                stride_t_toe_off: time of toe off in current stride
                t_onset: time of torque onset in current stride
                t_dropoff: time of torque dropoff in current stride
            """
            
            # Convert Nodes to % stride
            stride_t_peak = self.t_peak / END_OF_STRIDE * stride_period
            stride_t_rise = self.t_rise / END_OF_STRIDE * stride_period
            stride_t_fall = self.t_fall / END_OF_STRIDE * stride_period
            stride_t_toe_off = self.t_toe_off / END_OF_STRIDE * stride_period

            # calculate time of torque onset and dropoff
            stride_t_onset = stride_t_peak - stride_t_rise
            stride_t_dropoff = stride_t_peak + stride_t_fall

            return [stride_t_onset, stride_t_peak, stride_t_dropoff, stride_t_toe_off]
        