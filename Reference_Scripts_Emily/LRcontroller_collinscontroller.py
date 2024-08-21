# Emily Bywater
import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

from Emily_reference_code.CharacterizationFunctions_template import calibrateWrapper
from LRclass_template import ExoObject
from State_ZMQ import ZmqVICONpi

def torquetridiag(L, D, U, B, i_pk):
	n = len(B) 
	UU = np.concatenate((np.concatenate((np.zeros((n-1, 1)), np.diag(U)), axis=1), np.zeros((1, n))), axis=0)
	LL =np.concatenate((np.zeros((1, n)), np.concatenate((np.diag(L), np.zeros((n - 1, 1))), axis = 1)), axis=0)
	DD = UU + LL + np.diag(D)
	B[i_pk-1] = 0
	DD[i_pk-1] = np.zeros(np.shape(DD[i_pk-1]))
	DD[i_pk-1][i_pk-1] = 1
	B[0] = 0
	DD[0] = np.zeros(np.shape(DD[i_pk-1]))
	DD[0][0] = 1
	X = np.matmul(np.linalg.inv(DD), B)
	return X
	
def torquespline(x, y, i_pk, t):
	n = len(x)	
	h = np.array([])
	delta = np.array([])
	for i in range(0, n-1):
		h = np.insert(h, i, x[i+1] - x[i])
		delta = np.insert(delta, i, (y[i+1] - y[i])/h[i])
	hp = h[1:n-1]
	hm = h[0:n-2]
	deltap = delta[1:n-1]
	deltam = delta[0:n-2]
	L = np.append(hp, 1)
	D = 2*np.append(np.insert(hp+hm, 0, 1), 1)
	U = np.insert(hm, 0, 1)
	B = 3 * np.append(np.insert(np.multiply(hp,deltam) + np.multiply(hm, deltap), 0, delta[0]), delta[n-2])
	dy = torquetridiag(L, D, U, B, i_pk)
	if t <= x[0] or t >= x[n-1]:
		u = 0
	else:
		k = 0
		for i in range(0, n-2):
			if t >= x[i] and t <= x[i+1]:
				k = i
		a = delta[k]
		b = (a - dy[k])/h[k]
		c = (dy[k+1] - a)/h[k]
		d = (c - b)/h[k]
		u = y[k] + np.multiply(np.multiply(np.multiply((t - x[k]), dy[k] + t - x[k]), b + t - x[k+1]), d)
	return u
	

def curve_generator(tau_pk, t_on, t_off, t_pk):
	tau_nom = 2
	t_zero = 100
	t_ankor = np.array([t_on, t_pk, t_off])/100
	tau_ankor = np.array([0, tau_pk-tau_nom, 0])
	t = np.array(list(range(0, 101))) # %stance
	torque = np.array([])
	for i in range(0, 101):
		if t[i] < t_on:
			torque = np.insert(torque, i, tau_nom * t[i] / t_on, axis=None)
		elif t[i] > t_off:
			if t[i] < t_zero and t_zero > t_off:
				torque = np.insert(torque, i, tau_nom*(t_zero - t[i])/(t_zero - t_off), axis=None)
			else:
				torque = np.insert(torque, i, 0)
		else:
			torque = np.insert(torque, i, torquespline(t_ankor, tau_ankor, 2, t[i]/100) + tau_nom)
	torque_curve = np.array([np.transpose(t), np.transpose(torque)])	
	print(torque_curve)
	return torque_curve


def main(writer_Loop_l, writer_End_l, writer_Loop_r, writer_End_r, Vicon_data):
	# Change these
	tau_pk = 23.67 # Nm/kg
	t_on = 22.91 # %stance
	t_off = 96.46 # %stance
	t_pk = 75.71 # %stance
	torque_curve = curve_generator(tau_pk, t_on, t_off, t_pk)

	# To use the exos, it is necessary to define the ports they are going to be connected to. These are defined in the ports.yaml file in the flexsea repo
	port_cfg_path = '/home/pi/jump-exo/ports.yaml'
	ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

	# Always turn left exo on first for ports to line up or switch these numbers
	port_left = ports[0]
	port_right = ports[1]
	try:
		
		# CHARACTERIZE LEFT
		# Characterization includes getting the zero and the transmission ratio curve. 
		# Collect the transmission ratio when you start using the exos and anytime you replace the belts or periodically
		# Zero the exos every time you start this code
		side_left = "left"
		motorAngleOffset_deg_l, ankleAngleOffset_deg_l, \
			charCurve_poly_fit_l, TR_poly_fit_l = calibrateWrapper(side_left, port_left, baud_rate, recalibrateZero=True, recalibrateCurve=False)

		# CHARACTERIZE RIGHT
		side_right = "right"
		motorAngleOffset_deg_r, ankleAngleOffset_deg_r, \
			charCurve_poly_fit_r, TR_poly_fit_r = calibrateWrapper(side_right, port_right, baud_rate, recalibrateZero=True, recalibrateCurve=False)
		
		# Shouldn't need to change
		streamFreq = 1000 # Hz
		data_log = False  # False means no logs will be saved
		debug_logging_level = 6  # 6 is least verbose, 0 is most verbose

		# Load the devices and start them streaming
		fxs = flex.FlexSEA()
		dev_id_left = fxs.open(port_left, baud_rate, debug_logging_level)
		dev_id_right = fxs.open(port_right, baud_rate, debug_logging_level)
		fxs.start_streaming(dev_id_left, freq=streamFreq, log_en=data_log)
		fxs.start_streaming(dev_id_right, freq = streamFreq, log_en=data_log)
		app_type_right = fxs.get_app_type(dev_id_right)
		app_type_left = fxs.get_app_type(dev_id_left)

		input('Hit ENTER to send start commands to BOTH exos')

		# These three lines are only relevant if using the Vicon sync pi
		# Basically, don't start the procedure until receiving a signal of 1s from the Vicon pi (Vicon has started)
		Vicon_data = 0
		while Vicon_data == 0:
			Vicon_data = Vicon_synch.update()
		
		# Initialize an exo object on both the left and right sides that you can access to write your unique code.
		exoLeft = ExoObject(fxs, side_left, motorAngleOffset_deg_l, ankleAngleOffset_deg_l, charCurve_poly_fit_l, TR_poly_fit_l, dev_id_left, writer_Loop_l, writer_End_l, torque_curve)
		exoRight = ExoObject(fxs, side_right, motorAngleOffset_deg_r, ankleAngleOffset_deg_r, charCurve_poly_fit_r, TR_poly_fit_r, dev_id_right, writer_Loop_r, writer_End_r, torque_curve)
		
		i = 0
		globalStart = time()
		run_time_total = 60
		inProcedure = True

		# Iterate through your state machine controller that controls the exos until time runs out (or until you set a different end point)
		while inProcedure:

			i += 1

			currentTime = time() 
			run_time = currentTime - globalStart
			
			exoLeft.iterate(i, run_time)
			exoRight.iterate(i, run_time)

			if run_time >= run_time_total:
				inProcedure = False
		
	
	except:
		print('EXCEPTION: Stopped')
		print("broke: ")
		print(traceback.format_exc())

	finally:
		# Stop the motors and close the device IDs before quitting
		fxs.send_motor_command(dev_id_left, fxe.FX_NONE, 0)
		fxs.send_motor_command(dev_id_right, fxe.FX_NONE, 0)
		sleep(0.5)

		fxs.close(dev_id_left)
		fxs.close(dev_id_right)

		# Average frequency is a good indicator of efficiency (> 1000 is normal/good if you don't print too much)
		print("Average execution frequency: {}".format(float(i)/(currentTime - globalStart))  )
		print("END SCRIPT")


if __name__ == '__main__':

	# Create files to write the data to. Write to the loop files each iteration of the class. Write to the end files with any variables after all iterations are complete
	filename_LoopData_l = '{0}_jumping_controllerLoopData_l.csv'.format(strftime("%Y%m%d-%H%M%S"))
	filename_LoopData_r = '{0}_jumping_controllerLoopData_r.csv'.format(strftime("%Y%m%d-%H%M%S"))
	filename_EndData_l = '{0}_jumping_controllerEndData_l.csv'.format(strftime("%Y%m%d-%H%M%S"))
	filename_EndData_r = '{0}_jumping_controllerEndData_r.csv'.format(strftime("%Y%m%d-%H%M%S"))
	
	# If collecting data with Vicon, connect to a second pi which works with the Delsys system to synch data
	Vicon_synch = ZmqVICONpi(connectport="tcp://192.168.1.149:5555")

	# Open the new files and run the main function
	with open(filename_LoopData_l, "w", newline="\n") as fd_Loop_l:
		writer_Loop_l = csv.writer(fd_Loop_l)
		with open(filename_EndData_l, "w", newline='\n') as fd_End_l:
			writer_End_l = csv.writer(fd_End_l)
			with open(filename_LoopData_r, "w", newline="\n") as fd_Loop_r:
				writer_Loop_r = csv.writer(fd_Loop_r)
				with open(filename_EndData_r, "w", newline='\n') as fd_End_r:
					writer_End_r = csv.writer(fd_End_r)
					main(writer_Loop_l, writer_End_l, writer_Loop_r, writer_End_r, Vicon_synch)





