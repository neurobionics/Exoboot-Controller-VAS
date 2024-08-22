# Description:
# This script creates an ExoObject Class to pair with the main VAS controller python file for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running methods critical to the main control loop.
#
# Modified for VAS Vickrey protocol by: Nundini Rawal
# Date: 06/13/2024

import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np
import traceback
from typing import List, Tuple
from scipy import interpolate
from flexsea.device import Device
from assistance_generator import AssistanceGenerator
from thermal import ThermalModel
import config

class ExoObject:
    def __init__(self, side, device):
        # Necessary Inputs for Exo Class
        self.side = side
        self.device = device
        
        # Zeroes from homing procedure
        self.motorAngleOffset_deg = None
        self.ankleAngleOffset_deg = None

        # Transmission parameters (initialized to default)
        self.motor_angle_curve_coeffs = None
        self.TR_curve_coeffs = None
        self.max_dorsi_offset = None        # from TR_characterizer (max dorsiflexion angle)
        
        # Set Transmission Ratio and Motor-Angle Curve Coefficients	from pre-performed calibration
        self.load_TR_curve_coeffs()
        
        # Set Side multiplier and TR Coeffs
        # CHECK THESE BY MAKING SURE THE BELTS ARE NOT SPOOLING BACK ON THE LIP OF THE METAL SPOOL (CAUSES BREAKAGE)
        if self.side == "left": 
            self.exo_left_or_right_sideMultiplier = -1  # spool belt/rotate CCW for left exo
            self.ank_enc_sign = config.ANK_ENC_SIGN_LEFT_EXO
        elif self.side == "right":
            self.exo_left_or_right_sideMultiplier = -1#1   # spool belt/rotate CW for right exo
            self.ank_enc_sign = config.ANK_ENC_SIGN_RIGHT_EXO
        
        # Instantiate the four point spline algorithm
        self.bias_current:int = 750
        self.assistance_generator = AssistanceGenerator(bias_current=self.bias_current)
        
        # Instantiate Thermal Model and specify thermal limits
        self.thermalModel = ThermalModel(temp_limit_windings=100,soft_border_C_windings=10,temp_limit_case=70,soft_border_C_case=10)
        self.case_temperature = 0
        self.winding_temperature = 0
        self.max_case_temperature = 80
        self.max_winding_temperature = 115
        self.frequency = 175 #(in OSL Lib: 500)
        self.exo_safety_shutoff_flag = False

        # Unit Conversions (from Dephy Website, Units Section: https://dephy.com/start/#programmable_safety_features)
        self.degToCount = 45.5111  # counts/deg (16384 motor enc clicks/360°rotation)
        self.MOT_ENC_CLICKS_TO_DEG = 1 / self.degToCount  # degs/count (These are same value for both motor and ankle encoder)
        self.ANK_ENC_CLICKS_TO_DEG = 360 / 16384  # counts/deg

        # Motor Parameters
        self.efficiency = 0.9  # motor efficiency
        self.Kt = 0.000146  # N-m/mA motor torque constant
        self.Res_phase = 0.279  # ohms
        self.L_phase = 0.5 * 138 * 10e-6  # henrys
        self.CURRENT_THRESHOLD = config.MAX_ALLOWABLE_CURRENT  # mA
        
    def set_spline_timing_params(self, spline_timing_params):
        """ 
        Args:
        spline_timing_params:list = [t_rise, t_peak, t_fall, t_toe_off, holding_torque]
        """
        self.assistance_generator.t_rise = spline_timing_params[0]      # % stride from t_peak
        self.assistance_generator.t_peak = spline_timing_params[1]      # % stride from heel strike
        self.assistance_generator.t_fall = spline_timing_params[2]      # % stride from t_peak
        self.assistance_generator.t_toe_off = spline_timing_params[3]   # % stride from heel strike
        self.assistance_generator.holding_torque = spline_timing_params[4] 
        print("4-point spline params set")

    def spool_belt(self):
        self.device.command_motor_current(self.exo_left_or_right_sideMultiplier * self.bias_current)
        # self.fxs.send_motor_command(self.device, self.exo_left_or_right_sideMultiplier*self.bias_current)
        sleep(0.5)
        print("Belt spooled for: ", self.device.id)
        
    def zeroProcedure(self) -> Tuple[float, float]:
        """This function holds a current of 1000 mA for 1 second and collects ankle angle.
        If the ankle angle hasn't changed during this time, this is the zero. Otherwise, the 1 second hold repeats.
        Subject should stand still while this is running.

        returns:
                motorAngleOffset_deg (float): motor angle offset in degrees
                ankleAngleOffset_deg (float): ankle angle offset in degrees
        """
        filename = "Autogen_zeroing_coeff_files/offsets_Exo{}.csv".format(self.side.capitalize())

        # conduct zeroing/homing procedure and log offsets
        with open(filename, "w") as file:
            print("Starting ankle zeroing/homing procedure for: \n", self.side)
            
            pullCurrent = 1000  # mA
            iterations = 0
            holdingCurrent = True
            holdCurrent = pullCurrent * self.exo_left_or_right_sideMultiplier
            run_time_total = 1  # seconds
            moveVec = np.array([])
            motorAngleVec = np.array([])
            ankleAngleVec = np.array([])
            startTime = time()

            while holdingCurrent:
                print("in zeroing loop")
                iterations += 1
                currentTime = time()
                timeSec = currentTime - startTime

                # fxu.clear_terminal()
                if self.side == 'left':
                    current_mot_angle = config.motor_angle_left
                    current_ank_angle = config.ankle_angle_left

                    current_ank_vel = config.ankle_velocity_left  # Dephy multiplies ank velocity by 10 (rad/s)
                    current_mot_vel = config.motor_velocity_left
                else:
                    current_mot_angle = config.motor_angle_right
                    current_ank_angle = config.ankle_angle_right 

                    current_ank_vel = config.ankle_velocity_right  # Dephy multiplies ank velocity by 10 (rad/s)
                    current_mot_vel = config.motor_velocity_right

                self.device.command_motor_current(holdCurrent)
                
                print("Ankle Angle: {} deg...".format(current_ank_angle))

                # determines whether wearer has moved
                if (abs(current_mot_vel)) > 100 or (abs(current_ank_vel) > 1):
                    moveVec = np.append(moveVec, True)
                else:
                    moveVec = np.append(moveVec, False)

                motorAngleVec = np.append(motorAngleVec, current_mot_angle)
                ankleAngleVec = np.append(ankleAngleVec, current_ank_angle)

                # if the ankle angle hasn't changed during the hold time, determine offsets and exit loop
                if (timeSec) >= run_time_total:
                    if not np.any(moveVec):  # if none moved
                        self.motorAngleOffset_deg = np.mean(motorAngleVec)
                        self.ankleAngleOffset_deg = np.mean(ankleAngleVec)
                        if(self.side == 'left'):
                            config.ankle_offset_left = self.ankleAngleOffset_deg
                            config.motor_angle_offset_left = self.motorAngleOffset_deg
                        elif(self.side == 'right'):
                            config.ankle_offset_right = self.ankleAngleOffset_deg
                            config.motor_angle_offset_right = self.motorAngleOffset_deg
                        holdingCurrent = False

                    else:
                        print("retrying")
                        moveVec = np.array([])
                        motorAngleVec = np.array([])
                        ankleAngleVec = np.array([])
                        startTime = time()
                        iterations = 0
                        
            # ramp down
            print("Turning off Zero-ing Procedure Current Control...")
            print("Motor Angle offset: {} deg\n".format((self.motorAngleOffset_deg)))
            print("Ankle Angle offset: {} deg\n".format((self.ankleAngleOffset_deg)))

            writer = csv.writer(file, delimiter=",")
            writer.writerow([self.motorAngleOffset_deg, self.ankleAngleOffset_deg])
            file.close()
            
            self.device.command_motor_current(0)
            sleep(0.5)
     
    def load_TR_curve_coeffs(self):
        """Sets Transmission Ratio coefficients from a logged file. 
        Coefficients are a 4th order polynomial fit to the TR curve.
        After TR recalibration, the logged file will have different values.
        TR recalibration procedure should be re-done after belt 
        replacement/exo reassembly (script: TR_characterization_test.py).
        """
        # Open and read the CSV file
        try:  
            tr_coefs_filename = "Transmission_Ratio_Characterization/default_TR_coefs_{}.csv".format(self.side)
            with open(tr_coefs_filename, mode='r') as file:
                csv_reader = csv.reader(file)
                coefs_ankle_vs_motor = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
                coefs_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
                max_dorsiflexed_ang = next(csv_reader)
                
                # convert to array of real numbers to allow for polyval evaluation
                self.TR_curve_coeffs = [float(x) for x in coefs_TR]
                self.motor_angle_curve_coeffs = [float(y) for y in coefs_ankle_vs_motor]
                self.max_dorsi_offset = float(max_dorsiflexed_ang[0])

            if self.side == "left":
                config.max_dorsiflexed_ang_left = self.max_dorsi_offset
            elif self.side == "right":
                config.max_dorsiflexed_ang_right = self.max_dorsi_offset
        except:
            print("I hope you are doing TR characterization")
            return 0
        
        return self.TR_curve_coeffs
                
    def get_TR_for_ank_ang(self, curr_ank_angle):
        N = np.polyval(self.TR_curve_coeffs, curr_ank_angle)  # Instantaneous transmission ratio
        
        # Safety check to prevent current limit spikes past the allowable limit 
        # (ideally should not be limited to 10 and should go below)
        N = max(N, 10)
            
        if self.side == "left":
            config.N_left = N
        elif self.side == "right":
            config.N_right = N
            
        return N

    def desired_torque_2_current(self, desired_spline_torque):
        # convert desired torque to desired current
        if self.side == "left":
            curr_ank_angle = config.ankle_angle_left
        elif self.side == "right":
            curr_ank_angle = config.ankle_angle_right
        
        N = self.get_TR_for_ank_ang(curr_ank_angle)
            
        des_current = desired_spline_torque / (N * self.efficiency * self.Kt)   # output in mA
        
        return int(des_current)

    def max_current_safety_checker(self, commanded_current):
        """Safety Check for ActPack current"""
        if abs(commanded_current) >= config.MAX_ALLOWABLE_CURRENT:
            print("Exceeding current limits!!!")
            print("Current comanded is: ", commanded_current, " Limit is: ", config.MAX_ALLOWABLE_CURRENT)
            print("Setting current to max allowable current")
            new_commanded_current = config.MAX_ALLOWABLE_CURRENT
        else:
            new_commanded_current = commanded_current
            
        return new_commanded_current
    
    def thermal_safety_checker(self):
        """Ensure that winding temperature is below 100°C (115°C is the hard limit).
        Ensure that case temperature is below 75°C (80°C is the hard limit).
        Uses Jianpings model to project forward the measured temperature from Dephy ActPack.
        
        Returns:
        exo_safety_shutoff_flag (bool): flag that indicates if the exo has exceeded thermal limits. 
        Used to toggle whether the device should be shut off.
        """
            
        # measured temp by Dephy from the actpack is the case temperature
        if self.side == "left":
            measured_temp = config.temperature_left
            motor_current = config.motor_current_left
        elif self.side == "right":
            measured_temp = config.temperature_right 
            motor_current = config.motor_current_right
            
        # determine modeled case & winding temp
        self.thermalModel.T_c = measured_temp
        self.thermalModel.update(dt=(1 / self.frequency), motor_current=motor_current)
        self.winding_temperature = self.thermalModel.T_w

        # Shut off exo if thermal limits breached
        if measured_temp >= self.max_case_temperature:
            self.exo_safety_shutoff_flag = True 
            print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
        if self.winding_temperature >= self.max_winding_temperature:
            self.exo_safety_shutoff_flag = True 
            print("Winding Temperature has exceed 115°C soft limit. Exiting Gracefully")

        # using Jianping's thermal model to project winding & case temperature
        # using the updated case temperature and setting shut-off flag
        # self.case_temperature = measured_temp
        # exo_safety_shutoff_flag = self.get_modelled_temps(motor_current)
    
    def get_modelled_temps(self, motor_current)->bool:
        """using Jianping's thermal model to project winding & case 
        temperature and determine whether exo should be shut off
        
        Args:
        motor_current (float): measured motor current in mA
        
        Returns:
        exo_safety_shutoff_flag (float): flag that indicates if the exo has exceeded thermal limits. 
        Used to toggle whether the device should be shut off.
        """
        self.thermalModel.T_c = self.case_temperature
        self.thermalModel.update(dt=(1 / self.frequency), motor_current=motor_current)
        self.winding_temperature = self.thermalModel.T_w
        
        if self.case_temperature >= self.max_case_temperature:
            shutoff_flag = True 
            print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
        if self.winding_temperature >= self.max_winding_temperature:
            shutoff_flag = True 
            print("Winding Temperature has exceed 115°C soft limit. Exiting Gracefully soon")
        
        return shutoff_flag
    
    def iterate(self):
        
        # TO ENABLE TORQUE BASED FSM:
        if config.in_torque_FSM_mode:
            # TODO: if in_swing, pull the gui_commanded_torque (this way we don't change the peak torque during mid stance)
            if config.in_swing_bertec_left:
                self.peak_torque_left = config.GUI_commanded_torque
                
            if config.in_swing_bertec_right:
                self.peak_torque_right = config.GUI_commanded_torque
                
            if(self.side == 'left'):
                # 4-point spline generated torque
                # desired_spline_torque = self.assistance_generator.torque_generator_MAIN(config.time_in_current_stride_left, config.stride_time_left, peak_torque, config.in_swing_start_left)
                desired_spline_torque = self.assistance_generator.torque_generator_stance_MAIN(config.time_in_current_stance_left, 
                                                                                               config.stride_period_bertec_left, 
                                                                                               config.stance_time_left, 
                                                                                               self.peak_torque_left, 
                                                                                               config.in_swing_bertec_left)                
                # desired_spline_torque = self.assistance_generator.biomimetic_torque_generator_MAIN(config.time_in_current_stance_left, config.stance_time_left, peak_torque, config.in_swing_bertec_left)
                config.desired_spline_torque_left = desired_spline_torque
                
                
            elif(self.side == 'right'):
                # desired_spline_torque = self.assistance_generator.torque_generator_MAIN(config.time_in_current_stride_right, config.stride_time_right, peak_torque, config.in_swing_start_right)
                desired_spline_torque = self.assistance_generator.torque_generator_stance_MAIN(config.time_in_current_stance_right, 
                                                                                               config.stride_period_bertec_right, 
                                                                                               config.stance_time_right, 
                                                                                               self.peak_torque_right, 
                                                                                               config.in_swing_bertec_right)                 
                # desired_spline_torque = self.assistance_generator.biomimetic_torque_generator_MAIN(config.time_in_current_stance_right, config.stride_period_bertec_right,peak_torque, config.in_swing_bertec_right)
                config.desired_spline_torque_right = desired_spline_torque
            else:
                print("Error")
            
            # Convert spline torque to it's corresponding current (mA)
            desired_spline_current = self.desired_torque_2_current(desired_spline_torque)
        
        else:
            # TO ENABLE CURRENT BASED FSM:
            peak_current = config.GUI_commanded_torque*0.5
            
            if(self.side == "left"):
                # 4-point spline generated current
                desired_spline_current = self.assistance_generator.current_generator_stance_MAIN(config.time_in_current_stance_left, 
                                                                                               config.stride_period_bertec_left, 
                                                                                               config.stance_time_left, 
                                                                                               peak_current, 
                                                                                               config.in_swing_bertec_left)
                config.desired_spline_torque_left = desired_spline_current
                curr_ank_angle = config.ankle_angle_left
            elif(self.side == "right"):
                desired_spline_current = self.assistance_generator.current_generator_stance_MAIN(config.time_in_current_stance_right, 
                                                                                                config.stride_period_bertec_right, 
                                                                                                config.stance_time_right, 
                                                                                                peak_current, 
                                                                                                config.in_swing_bertec_right)

                config.desired_spline_torque_right = desired_spline_current
                curr_ank_angle = config.ankle_angle_right
            else:
                print("Error")
                
            # for current control, log the current transmission ratio:
            N = self.get_TR_for_ank_ang(curr_ank_angle)

        # Clamp current between bias and max allowable current
        vetted_current = max(min(desired_spline_current, config.MAX_ALLOWABLE_CURRENT), self.bias_current)
        
        # Perform thermal safety check on actpack
        # self.thermal_safety_checker()
        
        # Shut off exo if thermal limits breached
        if self.exo_safety_shutoff_flag:
            self.device.command_motor_current(0)
            config.EXIT_MAIN_LOOP_FLAG == True
        else:
            self.device.command_motor_current(self.exo_left_or_right_sideMultiplier * vetted_current)