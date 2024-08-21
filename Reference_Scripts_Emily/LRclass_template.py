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
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

import Gait_State_EstimatorThread_bad as gse
import FourPointSpline as fourPtSpline


class ExoObject:
    def __init__(
        self,
        fxs,
        side,
        motorAngleOffset_deg,
        ankleAngleOffset_deg,
        devID,
        GUI_commanded_torque,
        spline_timing_params,
        writer_loop=None,
        writer_end=None,
        polynomial_fit=None,
        TR_poly_fit=None,
        
    ):

        # Vary these
        self.ANK_ANGLE_STATE_THRESHOLD = 10
        self.NUM_STRIDES = 0

        # Inputs
        self.fxs = fxs
        self.side = side
        self.motorAngleOffset_deg = motorAngleOffset_deg
        self.ankleAngleOffset_deg = ankleAngleOffset_deg
        self.polynomial_fit = polynomial_fit
        self.TR_poly_fit = TR_poly_fit
        self.devID = devID
        self.writer_loop = writer_loop
        self.writer_end = writer_end

        # High-level control parameter inputs
        self.GUI_commanded_torque = GUI_commanded_torque
        self.t_rise = spline_timing_params[0]  # % stride from t_peak
        self.t_peak = spline_timing_params[1]  # % stride from heel strike
        self.t_fall = spline_timing_params[2]  # % stride from t_peak
        self.t_toe_off = 65  # % stride from heel strike

        # TODO: Instantiate the gait state estimator

        # Instantiate the four point spline algorithm
        time_in_current_stride = 0
        stride_period = 0
        self.holding_torque_threshold = 2  # Nm
        fourPtSpline_ = fourPtSpline.FourPointSpline(
            self.t_rise,
            self.t_peak,
            self.t_fall,
            self.t_toe_off,
            self.holding_torque_threshold,
        )

        # Unit Conversions
        self.degToCount = 45.5111  # counts/deg
        self.MOT_ENC_CLICKS_TO_DEG = 1 / self.degToCount  # degs/count
        self.ANK_ENC_CLICKS_TO_DEG = 360 / 16384  # counts/deg

        # Motor Parameters
        self.efficiency = 0.9  # motor efficiency
        self.Kt = 0.14  # N-m/A motor torque constant
        self.Res_phase = 0.279  # ohms
        self.L_phase = 0.5 * 138 * 10e-6  # henrys
        self.CURRENT_THRESHOLD = 27000  # mA

        # Initialize
        self.average_window = 100
        self.act_ank_torque = 0
        self.angleMean = 0
        self.timeSecLast = 0
        self.meanVel = 0
        self.des_current = 0
        self.bias_current = 750

        # Vectors
        self.ankleAngleVec = np.array([])

        # Side multiplier
        # CHECK THESE BY MAKING SURE THE BELTS ARE NOT SPOOLING BACK ON THE LIP OF THE METAL SPOOL (CAUSES BREAKAGE)
        self.exo_left_or_right_sideMultiplier = 1
        if self.side == "left":
            self.exo_left_or_right_sideMultiplier = -1
        elif self.side == "right":
            self.exo_left_or_right_sideMultiplier = 1

        # ActPack (Actuator Package)
        self.actPackState = self.fxs.read_device(self.devID)

        # Gains - CHANGE THESE DEFAULTS AS NEEDED
        self.fxs.set_gains(
            self.devID, 40, 400, 0, 0, 0, 128
        )  # DEFAULT FOR CURRENT CONTROL
        # self.fxs.set_gains(self.devID, 400, 50, 0, 0, 0, 0) # DEFAULT FOR FOR POSITION CONTROL

    def spool_belt(self):
        self.fxs.send_motor_command(self.devID, fxe.FX_CURRENT, self.bias_current)
        sleep(2)
        print("done: ", self.devID)

        # Stop the motors and close the device IDs before quitting
        self.fxs.send_motor_command(self.devID, fxe.FX_NONE, 0)

    def iterate(self, i, timeSec):

        self.actPackState = self.fxs.read_device(self.devID)

        # =======Read act_pack variables======
        act_mot_angle = self.exo_left_or_right_sideMultiplier * -(
            (self.actPackState.mot_ang * self.MOT_ENC_CLICKS_TO_DEG)
            - self.motorAngleOffset_deg
        )  # deg
        act_ank_angle = self.exo_left_or_right_sideMultiplier * (
            self.ANK_ENC_CLICKS_TO_DEG * self.actPackState.ank_ang
            - self.ankleAngleOffset_deg
        )  # deg
        act_ank_vel = (
            self.actPackState.ank_vel
        )  # deg/sec * 10 MAY NOT BE RELIABLE. POSSIBLY NEED self.ANK_ENC_CLICKS_TO_DEG AND self.exo_left_or_right_sideMultiplier
        imu_Accelx = self.actPackState.accelx  # bits
        imu_Accely = self.actPackState.accely  # bits
        imu_Accelz = self.actPackState.accelz  # bits
        imu_Gyrox = self.actPackState.gyrox  # bits
        imu_Gyroy = self.actPackState.gyroy  # bits
        imu_Gyroz = self.actPackState.gyroz  # bits
        act_current = self.actPackState.mot_cur  # mA
        act_voltage = self.actPackState.mot_volt  # mV
        batt_current = self.actPackState.batt_curr  # mA
        batt_voltage = self.actPackState.batt_volt  # mV
        mot_velocity = self.actPackState.mot_vel  # deg/sec
        mot_acceleration = self.actPackState.mot_acc  # rad/sec^2
        temperature = self.actPackState.temperature  # deg C

        # This error appears if the exos are power cycled before the code stops running
        if np.abs(act_current) > 30000:
            raise Exception("power cycle please")

        # =======Ankle Angle and Velocity Calculation======
        self.ankleAngleVec = np.append(self.ankleAngleVec, act_ank_angle)

        # If using ank angle to determine ank velocity not the ank velocity reading
        if i > self.average_window:
            self.angleMean = np.mean(
                self.ankleAngleVec[(i) - self.average_window : (i)]
            )

            dangdt = self.ankleAngleVec[(i) - 3 : (i)]
            dangdt = np.diff(dangdt) / (timeSec - self.timeSecLast)
            self.meanVel = np.mean(dangdt)

        # Averaging ank angle is a good low pass filter
        elif i < self.average_window:
            self.angleMean = np.mean(self.ankleAngleVec)

        # =======Gait State Estimator====
        # TODO: Implement a gait state estimator using the ankle angle and velocity to determine the current gait phase
        # example outputs:
        gait_phase = 0
        time_in_current_stride = 0.30  # in seconds
        stride_period = 1  # in seconds

        # =======Four Point Spline Algorithm for State Transitions & Actions ======
        desired_spline_torque = fourPtSpline.torque_generator_MAIN(
            time_in_current_stride, stride_period, self.GUI_commanded_torque
        )

        # convert desired torque to desired current
        N = np.polyval(
            self.TR_poly_fit, act_ank_angle
        )  # Instantaneous transmission ratio
        self.des_current = (
            desired_spline_torque / (N * self.efficiency * self.Kt) * 1000
        )  # mA

        # =======Send Commands======
        # The current limit is around 27000 mA:
        if np.abs(self.des_current) > 27000:
            self.des_current = self.exo_left_or_right_sideMultiplier * 27000

        # Current control if desired torque is greater than minimum holding torque, otherwise position control
        if desired_spline_torque >= self.holding_torque_threshold:
            self.fxs.send_motor_command(self.devID, fxe.FX_CURRENT, self.des_current)
            sleep(0.0001)
        else:
            self.fxs.send_motor_command(
                self.devID, fxe.FX_POSITION, self.des_motor_ang_unadjusted
            )

        # ====Calculate Delivered Ankle Torque from Measured Current====
        # Calculate ankle torque based on delivered current to log in the data file
        act_mot_torque = (
            act_current * self.Kt / 1000 / self.exo_left_or_right_sideMultiplier
        )  # in Nm
        self.act_ank_torque = act_mot_torque * N * self.efficiency

        # =======Write the data out======
        data_frame_vec = [
            i,
            round(timeSec, 6),
            act_current,
            act_mot_angle,
            act_ank_vel,
            act_ank_angle,
            N,
            self.act_ank_torque,
            imu_Accelx,
            imu_Accely,
            imu_Accelz,
            imu_Gyrox,
            imu_Gyroy,
            imu_Gyroz,
            self.state,
            act_voltage,
            batt_current,
            batt_voltage,
            self.meanVel,
            mot_velocity,
            mot_acceleration,
            temperature,
        ]

        # self.writer_loop.writerow(data_frame_vec)
        self.timeSecLast = timeSec

    def writingEnd(self):

        # Add variables that may only change once per cycle not every iteration to write them to a separate file at the end of each cyle
        endVec = [0]

        self.writer_end.writerow(endVec)

    def clear(self):
        # Use this function if you want to iterate a bunch, then reset stuff for a different activity without stopping the code. Add more things to reset as needed.
        self.ankleAngleVec = np.array([])  # Reset ankleAngleVec
        self.state = self.state0  # Reset state
        self.fxs.set_gains(
            self.devID, 40, 400, 0, 0, 0, 128
        )  # If you change the gains in the state machine, you need to change them back here
