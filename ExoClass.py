# Description:
# This script creates an ExoObject Class to pair with the main VAS controller python file for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running methods critical to the main control loop.
#
# Original template created by: Emily Bywater
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

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe
from FourPointSpline import FourPointSpline
from thermal import ThermalModel

import config

class ExoObject:
    def __init__(self, fxs, side, dev_id, stream_freq, data_log, debug_logging_level):

        # Necessary Inputs for Exo Class
        self.fxs = fxs
        self.side = side
        self.dev_id = dev_id
        
        # Specify Constants for Streaming/Logging Data
        self.stream_freq = stream_freq # Hz
        self.data_log = data_log  # False means no logs will be saved
        self.debug_logging_level = debug_logging_level  # 6 is least verbose, 0 is most verbose in terms of logging
        
        # Vary these (initialized to default)
        self.ANK_ANGLE_STATE_THRESHOLD = 10
        self.NUM_STRIDES = 0
        
        # Transmission parameters (initialized to default)
        self.motorAngleOffset_deg = None    # from zeroing/homing procedure
        self.ankleAngleOffset_deg = None    # from zeroing/homing procedure
        self.max_dorsi_offset = None        # from TR_characterizer (max dorsiflexion angle)
        self.motor_angle_curve_coeffs = None
        self.TR_curve_coeffs = []
        
        # Side multiplier
        # CHECK THESE BY MAKING SURE THE BELTS ARE NOT SPOOLING BACK ON THE LIP OF THE METAL SPOOL (CAUSES BREAKAGE)
        if self.side == "left": 
            self.exo_left_or_right_sideMultiplier = -1  # spool belt/rotate CCW for left exo
            self.ank_enc_sign = config.ANK_ENC_SIGN_LEFT_EXO
        elif self.side == "right":
            self.exo_left_or_right_sideMultiplier = -1#1   # spool belt/rotate CW for right exo
            self.ank_enc_sign = config.ANK_ENC_SIGN_RIGHT_EXO
        
        # Instantiate the four point spline algorithm
        self.holding_torque_threshold = 2  # Nm
        self.fourPtSpline = FourPointSpline()
        
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
        self.MOT_ENC_CLICKS_TO_DEG = 1 / self.degToCount  # degs/count #TODO: These are same value for both motor and ankle encoder
        self.ANK_ENC_CLICKS_TO_DEG = 360 / 16384  # counts/deg

        # Motor Parameters
        self.efficiency = 0.9  # motor efficiency
        self.Kt = 0.000146  # N-m/mA motor torque constant
        self.Res_phase = 0.279  # ohms
        self.L_phase = 0.5 * 138 * 10e-6  # henrys
        self.CURRENT_THRESHOLD = 25000  # mA

        # Initialize
        self.bias_current = 750

    def start_streaming(self):
        print(self.dev_id)
        self.fxs.start_streaming(self.dev_id, freq=self.stream_freq, log_en=self.data_log)
        self.fxs.set_gains(self.dev_id, config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)  
        print("streaming has begun")

    def read_act_pack(self):
        self.actPackState = self.fxs.read_device(self.dev_id)
        print("actpack state read")
        
    def set_spline_timing_params(self, spline_timing_params):
        """ 
        Args:
        spline_timing_params:list = [t_rise, t_peak, t_fall, t_toe_off, holding_torque]
        """
        self.fourPtSpline.t_rise = spline_timing_params[0]      # % stride from t_peak
        self.fourPtSpline.t_peak = spline_timing_params[1]      # % stride from heel strike
        self.fourPtSpline.t_fall = spline_timing_params[2]      # % stride from t_peak
        self.fourPtSpline.t_toe_off = spline_timing_params[3]   # % stride from heel strike
        self.fourPtSpline.holding_torque = spline_timing_params[4] 
        print("4-point spline params set")

    def stop_motor_commands(self):
        # Stop the motors and close the device IDs before quitting
        self.fxs.send_motor_command(self.dev_id, fxe.FX_NONE, 0)
        sleep(0.5)
        self.fxs.close(self.dev_id)
        print("motor stopped and dev_id channel closed")

    def spool_belt(self):
        self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, self.exo_left_or_right_sideMultiplier*self.bias_current)
        sleep(3)
        print("belt spooled for: ", self.dev_id)
        
    def zeroProcedure(self) -> Tuple[float, float]:
        """This function holds a current of 1000 mA for 1 second and collects ankle angle.
        If the ankle angle hasn't changed during this time, this is the zero. Otherwise, the 1 second hold repeats.
        Subject should stand still while this is running.

        returns:
                motorAngleOffset_deg (float): motor angle offset in degrees
                ankleAngleOffset_deg (float): ankle angle offset in degrees
        """
        if self.side == "left" or self.side == "l":
            filename = "offsets_ExoLeft.csv"
        elif self.side == "right" or self.side == "r":
            filename = "offsets_ExoRight.csv"

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

                fxu.clear_terminal()
                if self.side == 'left':
                    current_mot_angle = config.motor_angle_left#(self.actPackState.mot_ang * self.MOT_ENC_CLICKS_TO_DEG)  # convert motor encoder counts to angle in degrees
                    current_ank_angle = config.ankle_angle_left#(self.actPackState.ank_ang * self.ANK_ENC_CLICKS_TO_DEG)  # convert ankle encoder counts to angle in degrees

                    current_ank_vel = config.ankle_velocity_left  # Dephy multiplies ank velocity by 10 (rad/s)
                    current_mot_vel = config.motor_velocity_left#self.actPackState.mot_vel
                else:
                    current_mot_angle = config.motor_angle_right#(self.actPackState.mot_ang * self.MOT_ENC_CLICKS_TO_DEG)  # convert motor encoder counts to angle in degrees
                    current_ank_angle = config.ankle_angle_right#(self.actPackState.ank_ang * self.ANK_ENC_CLICKS_TO_DEG)  # convert ankle encoder counts to angle in degrees

                    current_ank_vel = config.ankle_velocity_right  # Dephy multiplies ank velocity by 10 (rad/s)
                    current_mot_vel = config.motor_velocity_right#self.actPackState.mot_vel

                desCurrent = holdCurrent

                self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, desCurrent)

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
            
            self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, 0)
            sleep(0.5)
    
    
    def load_TR_curve_coeffs(self):
        """Sets Transmission Ratio coefficients from a logged file. 
        Coefficients are a 4th order polynomial fit to the TR curve.
        After TR recalibration, the logged file will have different values.
        TR recalibration procedure should be re-done after belt 
        replacement/exo reassembly (script: TR_characterization_test.py).
        """
        # Open and read the CSV file
        if self.side == "left":
            with open('default_TR_coefs_left.csv', mode='r') as file:
                csv_reader = csv.reader(file)
                p_master = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
                p_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
                max_dorsiflexed_ang_left = next(csv_reader)
                
                # convert to array of real numbers to allow for polyval evaluation
                p_TR = [float(x) for x in p_TR]
                p_master = [float(y) for y in p_master]
                self.max_dorsi_offset = float(max_dorsiflexed_ang_left[0])
                config.max_dorsiflexed_ang_left = self.max_dorsi_offset
        
        elif self.side == "right":
            with open('default_TR_coefs_right.csv', mode='r') as file:
                csv_reader = csv.reader(file)
                p_master = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
                p_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
                max_dorsiflexed_ang_right = next(csv_reader)
                
                # convert to array of real numbers to allow for polyval evaluation
                p_TR = [float(x) for x in p_TR]
                p_master = [float(y) for y in p_master]
                self.max_dorsi_offset = float(max_dorsiflexed_ang_right[0])
                config.max_dorsiflexed_ang_right = self.max_dorsi_offset
                
        self.motor_angle_curve_coeffs = p_master
        self.TR_curve_coeffs = p_TR
        
        return p_TR 
        
    def OLD_TR_curve_calibration(self):
        """This function collects a curve of motor angle vs. ankle angle which is differentiated
        later to get a transmission ratio curve vs. ankle angle. The ankle joint should be moved through
        the full range of motion (starting at extreme plantarflexion to extreme dorsiflexion on repeat)
        while this is running.
        """
    
        print("Starting ankle transmission ratio procedure...\n")
        
        # conduct transmission ratio curve characterization procedure and store curve
        filename = "char_curve_{0}_{1}.csv".format(self.side, strftime("%Y%m%d-%H%M%S"))
        dataFileTemp = "characterizationFunctionDataTemp.csv"
        inProcedure = True
        motorAngleVec = np.array([])
        ankleAngleVec = np.array([])
        interval = 20  # seconds
        iterations = 0
        startTime = time()
    
        sleep(1)
        pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet
        desCurrent = pullCurrent * self.exo_left_or_right_sideMultiplier
        sleep(0.5)
        print("Begin rotating the angle joint starting from extreme plantarflexion to extreme dorsiflexion...\n")
        
        with open(dataFileTemp, "w", newline="\n") as fd:
            writer = csv.writer(fd)
            while inProcedure:
                iterations += 1
                fxu.clear_terminal()
                act_pack = self.fxs.read_device(self.dev_id)
                self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, desCurrent)

                current_ank_angle = (act_pack.ank_ang * self.ANK_ENC_CLICKS_TO_DEG)  # obtain ankle angle in deg
                current_mot_angle = (act_pack.mot_ang * self.MOT_ENC_CLICKS_TO_DEG)  # obtain motor angle in deg

                act_current = act_pack.mot_cur
                currentTime = time()

                # OLD way of adjusting angles that accomodated offsets. But since we don't know exactly what the standing
                # position is, it's better to just use the "raw" angles for the transmission ratio
                motorAngle_adj = self.exo_left_or_right_sideMultiplier * -(current_mot_angle - self.motorAngleOffset_deg)
                ankleAngle_adj = self.exo_left_or_right_sideMultiplier * (current_ank_angle - self.ankleAngleOffset_deg)

                motorAngleVec = np.append(motorAngleVec, motorAngle_adj)
                ankleAngleVec = np.append(ankleAngleVec, ankleAngle_adj)
                print("Motor Angle: {} deg\n".format(motorAngle_adj))
                print("Ankle Angle: {} deg\n".format(ankleAngle_adj))

                if (currentTime - startTime) > interval:
                    inProcedure = False
                    print("Exiting Transmission Ratio Procedure\n")
                    n = 50
                    for i in range(0, n):
                        self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, pullCurrent * (n - i) / n)
                        sleep(0.04)

                writer.writerow([iterations, desCurrent, act_current, motorAngle_adj, ankleAngle_adj])

        # fit a 4th order polynomial to the ankle and motor angles
        self.motor_angle_curve_coeffs = np.polyfit(ankleAngleVec, motorAngleVec, 4)  
        
        # polynomial deriv coefficients (derivative of the motor angle vs ankle angle curve yields the TR)
        self.TR_curve_coeffs = np.polyder(self.motor_angle_curve_coeffs)  

        print("Char curve")
        print(str(self.motor_angle_curve_coeffs))
        print("TR curve")
        print(str(self.TR_curve_coeffs))
        
        print("Exiting curve characterization procedure")
        self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, 0)
        sleep(0.5)
        
        with open(filename, "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(self.motor_angle_curve_coeffs)
            writer.writerow(self.TR_curve_coeffs)
            
        return ankleAngleVec, motorAngleVec
        
    def plot_TR_motor_angle_curves(self, ankleAngleVec, motorAngleVec):
        # plot motor-ankle angle graph
        plt.figure(1)
        plt.plot(ankleAngleVec, motorAngleVec)
        polyfitted_motor_angle_curve = np.polyval(self.motor_angle_curve_coeffs, ankleAngleVec)
        plt.plot(
            ankleAngleVec,
            polyfitted_motor_angle_curve,
            label="polyfit",
            linestyle="dashed",
        )
        plt.xlabel("ankle angle")
        plt.ylabel("motor angle")

        # plot TR curve (interpolate polyfit params in case it isn't accurate):
        plt.figure(2)
        TR_curve = np.polyval(self.TR_curve_coeffs, ankleAngleVec)
        plt.plot(ankleAngleVec, TR_curve, label="polyfit")
        pchip_TR_curve = interpolate.PchipInterpolator(ankleAngleVec, TR_curve)
        plt.plot(ankleAngleVec, pchip_TR_curve(ankleAngleVec), linewidth=5, label="pchip auto")
        
    def get_TR_for_ank_ang(self, curr_ank_angle, coefficients):
        # print(coefficients)
        N = np.polyval(coefficients, curr_ank_angle)  # Instantaneous transmission ratio

    def desired_torque_2_current(self, desired_spline_torque, TR_coeffs):
        # convert desired torque to desired current
        if self.side == "left":
            curr_ank_angle = config.ankle_angle_left
        elif self.side == "right":
            curr_ank_angle = config.ankle_angle_right
        
        N = self.get_TR_for_ank_ang(curr_ank_angle, TR_coeffs)
        
        # Safety check to prevent current limit breaches further on
        if N < 10:
            N = 10
            
        if self.side == "left":
            # print("Left TR: ", N)
            config.N_left = N
        elif self.side == "right":
            # print("Right TR:", N)
            config.N_right = N 
            
        des_current = (desired_spline_torque / 
                            (N * self.efficiency * self.Kt))   # output in mA
        return des_current

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
    
    def thermal_safety_checker(self, motor_current):
        """Ensure that winding temperature is below 100°C (115°C is the hard limit).
        Ensure that case temperature is below 75°C (80°C is the hard limit).
        Uses Jianpings model to project forward the measured temperature from Dephy ActPack.
        
        Args:
        motor_current (float): measured motor current in mA
        
        Returns:
        exo_safety_shutoff_flag (bool): flag that indicates if the exo has exceeded thermal limits. 
        Used to toggle whether the device should be shut off.
        """
            
        # measured temp by Dephy from the actpack is the case temperature
        if self.side == "left":
            measured_temp = config.temperature_left
        elif self.side == "right":
            measured_temp = config.temperature_right 
            
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
    
    def iterate(self, TR_coeffs):
        # print("Commanded torque ", config.GUI_commanded_torque)
        # print("L Stride T: ",config.stride_time_left)
        # print("R Stride T: ",config.stride_time_right)
        # peak_torque = config.GUI_commanded_torque
        
        # if(self.side == 'left'):
        #     # 4-point spline generated torque
        #     desired_spline_torque = self.fourPtSpline.torque_generator_MAIN(config.time_in_current_stride_left, config.stride_time_left, peak_torque)#,config.in_swing)
        #     config.desired_spline_torque_left = desired_spline_torque
        # elif(self.side == 'right'):
        #     desired_spline_torque = self.fourPtSpline.torque_generator_MAIN(config.time_in_current_stride_right, config.stride_time_right, peak_torque)#,config.in_swing)
        #     config.desired_spline_torque_right = desired_spline_torque
        # else:
        #     print("Error")
        
        # ## TO ENABLE CURRENT BASED FSM:
        current_command = config.GUI_commanded_torque*700
        # vetted_current = self.max_current_safety_checker(current_command)
        if current_command == 0:
            current_command = 1000
        
        if(self.side == "left"):
            print('left', current_command)
            # 4-point spline generated current
            desired_spline_current = self.fourPtSpline.current_generator_MAIN(config.time_in_current_stride_left, config.stride_time_left, current_command)
            config.desired_spline_torque_left = desired_spline_current
        elif(self.side == "right"):
            print('right', current_command)
            desired_spline_current = self.fourPtSpline.current_generator_MAIN(config.time_in_current_stride_right, config.stride_time_right, current_command)
            config.desired_spline_torque_right = desired_spline_current
        else:
            print("Error")
            
        # Convert spline torque to it's corresponding current
        # desired_spline_current = self.desired_torque_2_current(desired_spline_torque, TR_coeffs)
        
        # Check whether commanded current is above the maximum current threshold
        # vetted_current = self.max_current_safety_checker(desired_spline_current)
        # print(vetted_current)
        
        if desired_spline_current >= config.MAX_ALLOWABLE_CURRENT:
            vetted_current = config.MAX_ALLOWABLE_CURRENT
        else:
            vetted_current = desired_spline_current
        
        # Perform thermal safety check on actpack
        # if self.side == "left":
        #     motor_current = config.motor_current_left
        # elif self.side == "right":
        #     motor_current = config.motor_current_right
            
        # self.thermal_safety_checker(motor_current)
        
        # Shut off exo if thermal limits breached
        if self.exo_safety_shutoff_flag == True:
            self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, 0)
            # exit out of method and while loop
            config.EXIT_MAIN_LOOP_FLAG == True
        else: 
            # Current control if desired torque is greater than minimum holding torque, otherwise position control
            # if desired_spline_torque >= self.holding_torque_threshold:
            #     self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, self.exo_left_or_right_sideMultiplier * vetted_current)
            # else:
            #     self.fxs.send_motor_command(self.dev_id, fxe.FX_POSITION, self.exo_left_or_right_sideMultiplier * self.bias_current)
            
            if desired_spline_current >= self.bias_current:
                self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, self.exo_left_or_right_sideMultiplier * vetted_current)
            else:
                self.fxs.send_motor_command(self.dev_id, fxe.FX_POSITION, self.exo_left_or_right_sideMultiplier * self.bias_current)


