import datetime as dt #16384/rotation
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

# Need this file to to characterize the exoskeleton
from Emily_reference_code.newCharacterizationFunctions import calibrateWrapper

def main(writer_Loop):
	port_cfg_path = '/home/pi/jump-exo/ports.yaml'
	ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

	# port = ports[0] # left 
	port = ports[1] # right 
	sideMultiplier = 1 # right, -1 left
	side = "right"

	try:
		run_time_total = 30

		inProcedure = True
		
		motorAngleOffset_deg, ankleAngleOffset_deg, \
			charCurve_poly_fit, TR_poly_fit = calibrateWrapper(side, port, baud_rate, recalibrateZero=True, recalibrateCurve=False)

		streamFreq = 1000 # Hz
		data_log = False  # False means no logs will be saved
		debug_logging_level = 6  # 6 is least verbose, 0 is most verbose

		fxs = flex.FlexSEA()
		dev_id = fxs.open(port, baud_rate, debug_logging_level)
		fxs.start_streaming(dev_id, freq=streamFreq, log_en=data_log)

		input('Hit ENTER to send start commands to the exo')

		i = 0
		globalStart = time()
		startTime = time()
		degToCount = 45.5111 # counts/deg
		countToDeg = 1/degToCount # degs/count
		SCALE_FACTOR = 360/16384
		Kt = 0.14
		efficiency = 0.9 # CHOOSE THIS BEFORE STARTING

		while inProcedure:

			i += 1

			currentTime = time() 
			run_time = currentTime - globalStart
			timeSec = currentTime - startTime # seconds

			actPackState = fxs.read_device(dev_id)

			act_mot_angle = sideMultiplier * -((actPackState.mot_ang * countToDeg) - motorAngleOffset_deg) # deg
			act_ank_angle = sideMultiplier * (SCALE_FACTOR * actPackState.ank_ang - ankleAngleOffset_deg) # deg
			act_current = actPackState.mot_cur

			if np.abs(act_current) > 28000:
				raise Exception('act_current too high')

			N = np.polyval(TR_poly_fit, act_ank_angle)

			act_mot_torque = act_current*Kt/1000
			act_ank_torque = act_mot_torque*N*efficiency

			# CHOOSE THESE BEFORE STARTING
			fxs.set_gains(dev_id, 40, 400, 0, 0, 0, 128)

			des_ank_torque = -1 # N-m
			des_mot_torque = des_ank_torque/N/efficiency
			des_current = sideMultiplier * (-int(des_mot_torque / Kt * 1000))
			if np.abs(des_current) > 27000:	
				des_current = sideMultiplier * 27000
			fxs.send_motor_command(dev_id, fxe.FX_CURRENT, des_current)

			data_frame_vec = [i, round(timeSec, 6), des_current, act_current,
					 act_mot_angle, act_ank_angle, N, des_ank_torque,
					 act_ank_torque, des_mot_torque, act_mot_torque]
			writer_Loop.writerow(data_frame_vec)

			if run_time >= run_time_total:
				inProcedure = False
		
	
	except:
		print('EXCEPTION: Stopped')
		print("broke: ")
		print(traceback.format_exc())

	finally:
		fxs.send_motor_command(dev_id, fxe.FX_NONE, 0)
		sleep(0.5)

		fxs.close(dev_id)

		print("Average execution frequency: {}".format(float(i)/(currentTime - globalStart))  )
		print("END SCRIPT")


if __name__ == '__main__':

	filename_LoopData = '{0}_jumping_controllerLoopData.csv'.format(strftime("%Y%m%d-%H%M%S"))
	
	with open(filename_LoopData, "w", newline="\n") as fd_Loop:
		writer_Loop = csv.writer(fd_Loop)
		main(writer_Loop)