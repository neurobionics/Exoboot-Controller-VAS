# Emily Bywater 9/21/2022
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

# Real time plotting
from rtplot import client

class ExoObject:
	def __init__(self, fxs, side, motorAngleOffset_deg, ankleAngleOffset_deg, polynomial_fit, TR_poly_fit, devID, writer_loop, writer_end):
		
		# Vary these
		self.ANK_ANGLE_STATE_THRESHOLD = 10
		self.ANK_ANGLE_JUMP_THRESHOLD = 15
		self.MEAN_VEL_THRESHOLD = -50
		self.PLANTAR_THRESHOLD = -35
		self.CURRENTOFFSET =13500 # 13500 or 27000 depending on low or high torque condition.

		# self.MASS = 56.7 #kg CHANGE PER PERSON
		# self.jumpStandHeight = 76.5*0.0254 # m CHANGE PER PERSON

		# Inputs
		self.fxs = fxs
		self.side = side
		# if self.side == "left":
		# 	self.PLANTAR_THRESHOLD = -37

		self.motorAngleOffset_deg = motorAngleOffset_deg
		self.ankleAngleOffset_deg = ankleAngleOffset_deg
		self.polynomial_fit = polynomial_fit
		self.TR_poly_fit = TR_poly_fit
		self.devID = devID
		self.writer_loop = writer_loop
		self.writer_end = writer_end

		# Unit Conversions
		self.degToCount = 45.5111 # counts/deg
		self.countToDeg = 1/self.degToCount # degs/count
		self.SCALE_FACTOR = 360/16384
			
		# Constants
		self.bias = 750 # mA 
		self.n = 50
		self.j = 50
		self.slack_offset = 100
		self.average_window = 100 # Averages are taken over this many time steps
		self.r = 2
		self.K_SPRING = 0.1 # N-m/deg

		# Motor Parameters
		self.efficiency = 0.9 # motor efficiency
		self.Kt = 0.14 # N-m/A motor torque constant 
		self.Res_phase = 0.279 # ohms
		self.L_phase = 0.5*138*10e-6 # henrys
		
		# Initialize
		# self.OFFSET = -30.0 # des_ank_torque_workloop
		self.CURRENT_THRESHOLD = 27000
		self.act_ank_torque = 0
		self.des_ank_torque = 0
		# self.des_ank_torque_spring = 0
		# self.des_ank_torque_workloop = 0
		self.des_mot_torque = 0
		self.des_ank_torque_last = 0
		self.des_current = 0
		self.des_current_last = 0
		self.angleMean = 0
		self.meanVel = 0
		self.currentErrInt = 0
		self.timeSecLast = 0
		self.des_current_spring = 0
		self.des_current_workloop = 0
		
		# Vectors
		self.ankleAngleVec = np.array([])
	
		# Define state variables
		self.state0 = 0 
		self.state1 = 1
		self.state2 = 2
		self.state = self.state0
		self.state3 = 3
		
		# Booleans
		self.squatted = 0
		self.right_transition = 0
		self.left_transition = 0
		self.meanVelBool = 0
		self.des_current_jumped = 1
		self.end = 0
		self.loop1 = 0

		# Jump height calculation
		self.act_ank_torqueVec = np.array([])
		self.ankAngleVelVecJump = np.array([])
		self.timeVecJump = np.array([])
		self.currentVec = np.array([])
		self.voltageVec = np.array([])
		self.expectedHeight = 0
		# self.actHeight = 0
		self.numSticks = 0
		# self.stickDist = 0.0254 # m Check this
		self.g = 9.81 # m/s^2 

		# Side multiplier
		self.sideMultiplier = 1	
		if (self.side == "left"):
			self.sideMultiplier = -1
		elif (self.side == "right"):
			self.sideMultiplier = 1

		# ActPack
		self.actPackState = self.fxs.read_device(self.devID)

		self.fxs.set_gains(self.devID, 100, 400, 0, 0, 0, 0)

		#4/11/23
		self.act_ank_angle = 0
		self.act_current = 0

	def iterate(self, i, timeSec, JUMP):

		self.actPackState = self.fxs.read_device(self.devID)
			
		# Read act_pack variables
		act_mot_angle = self.sideMultiplier * -((self.actPackState.mot_ang * self.countToDeg) - self.motorAngleOffset_deg) # deg
		self.act_ank_angle = self.sideMultiplier * (self.SCALE_FACTOR * self.actPackState.ank_ang - self.ankleAngleOffset_deg) # deg
		imu_Accel = self.actPackState.accelx 
		self.act_current = self.actPackState.mot_cur
		act_voltage = self.actPackState.mot_volt
		batt_current = self.actPackState.batt_curr
		batt_voltage = self.actPackState.batt_volt
		mot_velocity = self.actPackState.mot_vel
		temperature = self.actPackState.temperature
		
		N = np.polyval(self.TR_poly_fit, self.act_ank_angle)
		act_mot_torque = self.act_current*self.Kt/1000/self.sideMultiplier
		self.act_ank_torque = act_mot_torque*N*self.efficiency

		self.ankleAngleVec = np.append(self.ankleAngleVec, self.act_ank_angle)

		if i > self.average_window:
			self.angleMean = np.mean(self.ankleAngleVec[(i) - self.average_window : (i)])

			dangdt = self.ankleAngleVec[(i) - 3 : (i)]
			dangdt = np.diff(dangdt)/(timeSec-self.timeSecLast)
			self.meanVel = np.mean(dangdt)

		elif i < self.average_window:
			self.angleMean = np.mean(self.ankleAngleVec)
		
		if np.abs(self.act_current) > 30000:
			raise Exception('act_current too high')

		#=======State Transitions====== 
		if self.state == self.state0:
			if self.angleMean > self.ANK_ANGLE_STATE_THRESHOLD and JUMP == 0:
				self.state = self.state1
				
				print(f'{self.side} to state 1')
		elif self.state == self.state1:
			if self.act_ank_angle > self.ANK_ANGLE_JUMP_THRESHOLD:
				self.squatted = 1
			if (self.squatted==1 and self.meanVel < self.MEAN_VEL_THRESHOLD):
				self.meanVelBool = 1
				if self.side == 'left':
					self.left_transition = 1
				if self.side == 'right':
					self.right_transition = 1
			if JUMP == 1:
				self.state = self.state2
				self.fxs.set_gains(self.devID, 100, 500, 0, 0, 0, 128)
				sleep(0.001)
				print(f'{self.side} to state 2')
		elif self.state == self.state2:
			if self.des_current_jumped == 0:
				self.state = self.state3
				print(f'{self.side} to state 3')
				self.fxs.set_gains(self.devID, 400, 50, 0, 0, 0, 0) # default is 400, 50...
		if self.state == self.state3:
			
			self.end = 1
		
		#=======State Actions====== 
		if self.state == self.state0: # Stationary
			self.des_current = self.bias*self.sideMultiplier
	
		elif self.state == self.state1: # Squat
			self.des_ank_torque_last = self.des_ank_torque
			self.des_current_last = self.des_current

			self.des_ank_torque = self.K_SPRING * -self.act_ank_angle # this torque should always be negative
			if (self.des_ank_torque > 0):
				self.des_ank_torque = 0
			
			# Prevent torque and current from decreasing in state 1, especially right before the jump.
			if self.des_ank_torque > self.des_ank_torque_last: 
				self.des_ank_torque = self.des_ank_torque_last
			
			self.des_mot_torque = self.des_ank_torque/N/self.efficiency
			self.des_current = self.sideMultiplier * (-int(self.des_mot_torque / self.Kt * 1000) + self.bias) #mA
			
			if self.sideMultiplier* self.des_current < self.sideMultiplier*self.des_current_last:
				self.des_current = self.des_current_last

			if np.abs(self.des_current) > 27000:
				self.des_current = self.sideMultiplier * 27000
					
		elif self.state == self.state2: # Jump
			
			if self.des_current_jumped == 0:
				self.des_current = self.sideMultiplier * self.bias
			else:
				# Redefine self.des_ank_torque and current
				if self.loop1 == 0:
					# self.des_ank_torque_spring = self.des_ank_torque
					self.des_current_spring = self.des_current/self.sideMultiplier
					self.loop1 = 1
				if self.j >= 0:
					# self.des_ank_torque_workloop = int(self.OFFSET * (self.n-self.j)/self.n)
					self.des_current_workloop = int(self.CURRENTOFFSET * (self.n-self.j)/self.n)
					self.j = self.j - self.r
				else:
					# self.des_ank_torque_workloop = int(self.OFFSET)
					self.des_current_workloop = self.CURRENTOFFSET

				# self.des_ank_torque = self.des_ank_torque_spring + self.des_ank_torque_workloop
				# if self.des_ank_torque > 0:
				# 	self.des_ank_torque = 0
				# if self.des_ank_torque > self.des_ank_torque_last: 
				# 	self.des_ank_torque = self.des_ank_torque_last
				# des_ank_torque negative, transmission ratio positive -> des_mot_torque negative
				# self.des_mot_torque = self.des_ank_torque/N/self.efficiency
				# self.des_current = self.sideMultiplier * (-int(self.des_mot_torque / self.Kt * 1000) + self.bias) #mAa
				self.des_current = self.sideMultiplier * (self.des_current_spring + self.des_current_workloop)

				if self.sideMultiplier* self.des_current < self.sideMultiplier*self.des_current_last:
					self.des_current = self.des_current_last

				
				
				#SOFT LIMIT DES CURRENT
				if np.abs(self.des_current) > self.CURRENT_THRESHOLD:
					self.des_current = self.sideMultiplier * self.CURRENT_THRESHOLD

				self.des_current_last = self.des_current
				# self.des_ank_torque_last = self.des_ank_torque

				# self.currentVec = np.append(self.currentVec, act_current)
				# self.voltageVec = np.append(self.voltageVec, act_voltage)

				# self.act_ank_torqueVec = np.append(self.act_ank_torqueVec, self.act_ank_torque)
				# self.ankAngleVelVecJump = np.append(self.ankAngleVelVecJump, act_ank_angle)
				# self.timeVecJump = np.append(self.timeVecJump, timeSec)

			# Detect plantar flex at jump peak
			if (self.act_ank_angle < self.PLANTAR_THRESHOLD):

				self.des_current_jumped = 0
				self.end = 1

				self.des_current = self.sideMultiplier * self.bias

				# timeVecDiff = np.diff(self.timeVecJump)
				# timeVecDiff = np.concatenate((timeVecDiff[0], timeVecDiff), axis = None)
				# self.ankAngleVelVecJump = np.diff(self.ankAngleVelVecJump)
				# self.ankAngleVelVecJump = np.concatenate((self.ankAngleVelVecJump[0], self.ankAngleVelVecJump), axis = None)/timeVecDiff
				# powerVec = self.act_ank_torqueVec * self.ankAngleVelVecJump * np.pi/180
				# powerVecE = self.currentVec * self.voltageVec
				# Energy = np.trapz(powerVec, timeVecDiff)
				# EnergyE = np.trapz(powerVecE, timeVecDiff)
				# self.expectedHeight = Energy / (self.MASS*self.g)
				# self.expectedHeightE = EnergyE / (self.MASS*self.g)

		elif self.state == self.state3:
			angle = np.polyval(self.polynomial_fit, self.act_ank_angle) + self.slack_offset
			self.motorAngle_un_adj = ((angle / -self.sideMultiplier) + self.motorAngleOffset_deg) / self.countToDeg 

		# predictedCurrent = (act_voltage - mot_velocity*(np.pi/180)*self.Kt*1000)/self.Res_phase
		# currentDiff = self.des_current - act_current
		# self.currentErrInt += currentDiff
		# KpI = 0.1 #.12 #.21
		# KiI = 0 #3e-4 #4e-4
		# a = 0.5 #.6
		# des_voltage = KpI*currentDiff + KiI*self.currentErrInt + self.des_current*self.Res_phase + a*mot_velocity*(np.pi/180)*self.Kt*1000
		

		if self.state == self.state3:
			self.fxs.send_motor_command(self.devID, fxe.FX_POSITION, self.motorAngle_un_adj)
		if self.state == self.state1 or self.state==self.state0:
			self.fxs.send_motor_command(self.devID, fxe.FX_CURRENT, self.des_current)
			# sleep(0.001)
		else:
			self.fxs.send_motor_command(self.devID, fxe.FX_CURRENT, self.des_current)
			sleep(0.0001)
			
			
			# self.fxs.send_motor_command(self.devID, fxe.FX_VOLTAGE, des_voltage)
		
		

		# WRITE THE DATA OUT
		data_frame_vec = [i, round(timeSec,6), self.des_current, self.act_current, act_mot_angle, self.act_ank_angle, N, self.des_ank_torque,
		self.act_ank_torque, imu_Accel, self.state, JUMP, self.squatted, self.meanVelBool, act_voltage, batt_current, batt_voltage, self.des_mot_torque,
		self.meanVel, mot_velocity, temperature, self.des_current_workloop, self.des_current_spring]

		self.writer_loop.writerow(data_frame_vec)
		self.timeSecLast = timeSec

	def jumpHeight(self):

		# Input stick number to get actual height
		self.numSticks = int(input('Number of sticks hit: '))
		# self.actHeight = self.jumpStandHeight + self.stickDist*(self.numSticks - 1) 

		# Write out height and ankle angle difference data
		endVec = [self.numSticks]

		self.writer_end.writerow(endVec)

	def clear(self):
		self.des_ank_torque_last = 0
		self.ankleAngleVelVec = np.array([])
		self.ankleAngleVec = np.array([])
		self.currentVec = np.array([])
		self.voltageVec = np.array([])
		self.state = self.state0
		self.des_ank_torque = 0
		self.j = 50
		self.currentVec = np.array([])
		self.voltageVec = np.array([])
		self.act_ank_torqueVec = np.array([])
		self.ankAngleVelVecJump = np.array([])
		self.timeVecJump = np.array([])
		self.squatted = 0
		self.right_transition = 0
		self.left_transition = 0
		self.meanVelBool = 0
		self.des_current_jumped = 1
		self.meanVel = 0
		self.end = 0
		self.fxs.set_gains(self.devID, 100, 400, 0, 0, 0, 0)
		self.loop1 = 0


