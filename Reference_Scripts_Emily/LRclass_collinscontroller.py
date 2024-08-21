# Emily Bywater
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


class ExoObject:
	def __init__(self, fxs, side, motorAngleOffset_deg, ankleAngleOffset_deg, polynomial_fit, TR_poly_fit, devID, writer_loop, writer_end, torque_curve):


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
		self.torque_curve = torque_curve

		# Unit Conversions
		self.degToCount = 45.5111 # counts/deg
		self.countToDeg = 1/self.degToCount # degs/count
		self.SCALE_FACTOR = 360/16384
		
		# Motor Parameters
		self.efficiency = 0.9 # motor efficiency
		self.Kt = 0.14 # N-m/A motor torque constant 
		self.Res_phase = 0.279 # ohms
		self.L_phase = 0.5*138*10e-6 # henrys
		self.CURRENT_THRESHOLD = 27000
		
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
	
		# Define state variables
		self.state0 = 0 
		self.state1 = 1
		self.state2 = 2
		## ADD MORE STATES AS NEEDED
		self.state = self.state0
		

		# Side multiplier
		# CHECK THESE BY MAKING SURE THE BELTS ARE NOT SPOOLING BACK ON THE LIP OF THE METAL SPOOL (CAUSES BREAKAGE)
		self.sideMultiplier = 1	
		if (self.side == "left"):
			self.sideMultiplier = -1
		elif (self.side == "right"):
			self.sideMultiplier = 1

		# ActPack (Actuator Package)
		self.actPackState = self.fxs.read_device(self.devID)

		# Gains - CHANGE THESE DEFAULTS AS NEEDED
		self.fxs.set_gains(self.devID, 40, 400, 0, 0, 0, 128) # DEFAULT FOR CURRENT CONTROL
		# self.fxs.set_gains(self.devID, 400, 50, 0, 0, 0, 0) # DEFAULT FOR FOR POSITION CONTROL

		# Variables for gait detection
		self.stance = 0
		self.swing = 0
		self.percStance = 0
		self.des_torque = 0

	def iterate(self, i, timeSec):

		self.actPackState = self.fxs.read_device(self.devID)
			
		#=======Read act_pack variables======
		act_mot_angle = self.sideMultiplier * -((self.actPackState.mot_ang * self.countToDeg) - self.motorAngleOffset_deg) # deg
		act_ank_angle = self.sideMultiplier * (self.SCALE_FACTOR * self.actPackState.ank_ang - self.ankleAngleOffset_deg) # deg
		act_ank_vel = self.actPackState.ank_vel # deg/sec * 10 MAY NOT BE RELIABLE. POSSIBLY NEED self.SCALE_FACTOR AND self.sideMultiplier 
		imu_Accelx = self.actPackState.accelx # bits
		imu_Accely = self.actPackState.accely # bits
		imu_Accelz = self.actPackState.accelz # bits
		imu_Gyrox = self.actPackState.gyrox # bits
		imu_Gyroy = self.actPackState.gyroy # bits
		imu_Gyroz = self.actPackState.gyroz # bits
		act_current = self.actPackState.mot_cur # mA
		act_voltage = self.actPackState.mot_volt # mV
		batt_current = self.actPackState.batt_curr # mA
		batt_voltage = self.actPackState.batt_volt # mV
		mot_velocity = self.actPackState.mot_vel # deg/sec
		mot_acceleration = self.actPackState.mot_acc # rad/sec^2
		temperature = self.actPackState.temperature # deg C
		
		# Instantaneous transmission ratio
		N = np.polyval(self.TR_poly_fit, act_ank_angle)

		act_mot_torque = act_current*self.Kt/1000/self.sideMultiplier
		self.act_ank_torque = act_mot_torque*N*self.efficiency

		self.ankleAngleVec = np.append(self.ankleAngleVec, act_ank_angle)

		# If using ank angle to determine ank velocity not the ank velocity reading
		if i > self.average_window:
			self.angleMean = np.mean(self.ankleAngleVec[(i) - self.average_window : (i)])

			dangdt = self.ankleAngleVec[(i) - 3 : (i)]
			dangdt = np.diff(dangdt)/(timeSec-self.timeSecLast)
			self.meanVel = np.mean(dangdt)

		# Averaging ank angle is a good low pass filter
		elif i < self.average_window:
			self.angleMean = np.mean(self.ankleAngleVec)
		
		# This error gets thrown if the exos are power cycled before the code stops running
		if np.abs(act_current) > 30000:
			raise Exception('power cycle please')

		#=======State Transitions====== 
		if self.state == self.state0:
			# Condition for transitioning to new state goes here...
			if self.stance == 1:
				self.state = self.state1
				print(f'{self.side} to state 1') # Print when you're changing states
		# Add elif and else statements to facilitate further state transitions...
		elif self.state == self.state1:
			if self.swing == 1:
				self.state == self.state2
				print(f'{self.side} to state 2')
		
		#=======State Actions====== 
		if self.state == self.state0: # Stationary
			# Things that need to happen in this state go here...
			self.des_current = self.sideMultiplier * self.bias_current
		# Add elif and else statements to facilitate further state actions...
		elif self.state == self.state1:
			percStanceRounded = round(self.percStance)
			if self.percStance == self.percStanceRounded:
				self.des_torque = self.torque_curve[perStanceRounded]
			elif self.percStance > percStanceRounded:
				percStanceUp = percStanceRounded + 1
				self.des_torque = percStanceRounded + ((self.percStance - percStanceRounded)/(percStanceUp - percStanceRounded))*(percStanceUp - percStanceRounded)
			elif self.percStance < percStanceRounded:
				percStanceDown = percStanceRounded - 1
				self.des_torque = percStanceDown + ((self.percStance - percStanceDown)/(percStanceRounded - percStanceDown))*(percStanceRounded - percStanceDown)
			self.des_current = self.sideMultiplier * self.des_torque / self.Kt * 1000
		elif self.state == self.state2:
			self.des_current = 0

		#=======Send Commands======
		# Always provide limits just in case. If using current it may look something like (The current limit is around 27000 mA): 
		if np.abs(self.des_current) > 27000:
				self.des_current = self.sideMultiplier * 27000

		if self.state == self.state0 or self.state == self.state1:
			# self.fxs.send_motor_command(self.devID, fxe.FX_POSITION, self.des_motor_ang_unadjusted) # Syntax for position command
			self.fxs.send_motor_command(self.devID, fxe.FX_CURRENT, self.sideMultiplier * 750) # Syntax for current command (where 750 would be the desired current in mA independent of side)
		# Add elif and else statements based on state	
		elif self.state == self.state2:
			self.fxs.send_motor_command(self.devID, fxe.FX_NONE, 0)
			
		

		#=======Write the data out======
		# Add to this vector as desired
		data_frame_vec = [i, round(timeSec,6), act_current, act_mot_angle, act_ank_vel, act_ank_angle, N,
		self.act_ank_torque, imu_Accelx, imu_Accely, imu_Accelz, imu_Gyrox, imu_Gyroy, imu_Gyroz, self.state, act_voltage, batt_current, batt_voltage,
		self.meanVel, mot_velocity, mot_acceleration, temperature]

		self.writer_loop.writerow(data_frame_vec)
		self.timeSecLast = timeSec


	def writingEnd(self):

		# Add variables that may only change once per cycle not every iteration to write them to a separate file at the end of each cyle
		endVec = [0]

		self.writer_end.writerow(endVec)

	def clear(self):
		# Use this function if you want to iterate a bunch, then reset stuff for a different activity without stopping the code. Add more things to reset as needed. 
		self.ankleAngleVec = np.array([]) # Reset ankleAngleVec
		self.state = self.state0 # Reset state
		self.fxs.set_gains(self.devID, 40, 400, 0, 0, 0, 128) # If you change the gains in the state machine, you need to change them back here

