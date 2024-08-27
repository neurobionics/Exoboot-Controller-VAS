import datetime as dt #16384/rotation
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np
from rtplot import client 

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

from newCharacterizationFunctions import calibrateWrapper
from LRclass import ExoObject
from State_ZMQ import ZmqVICONpi
from ViconMan import Vicon
vicon = Vicon(viconPC_IP='141.212.77.16', viconPC_port=30)


def main(writer_Loop_l, writer_End_l, writer_Loop_r, Vicon_data):

	port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
	ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

	port_left = ports[0]
	port_right = ports[1]

	try:
		# vicon.start_recording('testingTrigger')
		plot_1_config = {'names': ['Current (A) Left', 'Current (A) Right'],
            'title': "Current (A) vs. Sample",
            'ylabel': "Current (A)",
            'xlabel': 'Sample', 
            'yrange': [0, 30],
            "colors":['red','blue'],
            "line_width":[8,8]
            }
		plot_2_config = {'names': ['Ankle Angle (deg) Left', 'Ankle Angle (deg) Right'],
            'title': "Ankle Angle (deg) vs. Sample",
            'ylabel': "Ankle Angle (deg)",
            'xlabel': 'Sample',
            'yrange': [-40, 40],
            "colors":['red','blue'],
            # "line_style":['-','-'],
            "line_width":[8,8]
            }
		
		plot_config = [plot_1_config,plot_2_config]
		client.initialize_plots(plot_config)
		input('Hit ENTER if plot initialized')
		run_time_total = 100*60

		inProcedure = True

		# CHARACTERIZE LEFT
		side_left = "left"
		motorAngleOffset_deg_l, ankleAngleOffset_deg_l, \
			charCurve_poly_fit_l, TR_poly_fit_l = calibrateWrapper(side_left, port_left, baud_rate, recalibrateZero=True, recalibrateCurve=False)
		# CHARACTERIZE RIGHT
		side_right = "right"
		motorAngleOffset_deg_r, ankleAngleOffset_deg_r, \
			charCurve_poly_fit_r, TR_poly_fit_r = calibrateWrapper(side_right, port_right, baud_rate, recalibrateZero=True, recalibrateCurve=False)

		streamFreq = 1000 # Hz
		data_log = False  # False means no logs will be saved
		debug_logging_level = 6  # 6 is least verbose, 0 is most verbose

		fxs = flex.FlexSEA()
		dev_id_left = fxs.open(port_left, baud_rate, debug_logging_level)
		dev_id_right = fxs.open(port_right, baud_rate, debug_logging_level)
		fxs.start_streaming(dev_id_left, freq=streamFreq, log_en=data_log)
		fxs.start_streaming(dev_id_right, freq = streamFreq, log_en=data_log)
		app_type_right = fxs.get_app_type(dev_id_right)
		app_type_left = fxs.get_app_type(dev_id_left)

		input('Hit ENTER to send start commands to BOTH exos')

		vicon.start_recording('Jump-w-h-p05')
	

		# Vicon_data = 0
		# while Vicon_data == 0:
		# 	Vicon_data = Vicon_synch.update()
	
		print('vicon on')
		exoLeft = ExoObject(fxs, side_left, motorAngleOffset_deg_l, ankleAngleOffset_deg_l, charCurve_poly_fit_l, TR_poly_fit_l, dev_id_left, writer_Loop_l, writer_End_l)
		exoRight = ExoObject(fxs, side_right, motorAngleOffset_deg_r, ankleAngleOffset_deg_r, charCurve_poly_fit_r, TR_poly_fit_r, dev_id_right, writer_Loop_r, writer_End_l)
		
		i = 0
		JUMP = 0
		globalStart = time()
		# startTime = time()

		while inProcedure:

			i += 1

			currentTime = time() 
			run_time = currentTime - globalStart
			# timeSec = currentTime - startTime # seconds

			exoLeft.iterate(i, run_time, JUMP)
			exoRight.iterate(i, run_time, JUMP)
			if i % 5 == 0:
				plot_data_array = [-exoLeft.act_current/1000,
								exoRight.act_current/1000,
								exoLeft.act_ank_angle,
								exoRight.act_ank_angle]
			
				client.send_array(plot_data_array)
			
			if(exoLeft.left_transition == 1 and exoRight.right_transition == 1):
				JUMP = 1

			if (exoLeft.end==1 and exoRight.end == 1):
				fxs.set_gains(dev_id_left, 40, 400, 0, 0, 0, 0)
				fxs.set_gains(dev_id_right, 40, 400, 0, 0, 0, 0)
				fxs.send_motor_command(dev_id_left, fxe.FX_CURRENT, -750)
				fxs.send_motor_command(dev_id_right, fxe.FX_CURRENT, 750)
				# vicon.stop_recording()
				# exoLeft.jumpHeight()
				exoLeft.clear()
				exoRight.clear()
				# vicon.stop_recording()
				JUMP = 0
				inProcedure = False
				print('Jump Complete!')


			if run_time >= run_time_total:
				inProcedure = False
		
	
	except:
		print('EXCEPTION: Stopped')
		print("broke: ")
		print(traceback.format_exc())

	finally:
		fxs.send_motor_command(dev_id_left, fxe.FX_NONE, 0)
		fxs.send_motor_command(dev_id_right, fxe.FX_NONE, 0)
		sleep(0.5)

		fxs.close(dev_id_left)
		fxs.close(dev_id_right)

		print("Average execution frequency: {}".format(float(i)/(currentTime - globalStart))  )
		print("END SCRIPT")


if __name__ == '__main__':

	filename_LoopData_l = '{0}_jumping_controllerLoopData_l.csv'.format(strftime("%Y%m%d-%H%M%S"))
	filename_EndData_l = '{0}_jumping_controllerEndData_l.csv'.format(strftime("%Y%m%d-%H%M%S"))
	filename_LoopData_r = '{0}_jumping_controllerLoopData_r.csv'.format(strftime("%Y%m%d-%H%M%S"))
	
	
	Vicon_synch = ZmqVICONpi(connectport="tcp://192.168.1.149:5555")

	with open(filename_LoopData_l, "w", newline="\n") as fd_Loop_l:
		writer_Loop_l = csv.writer(fd_Loop_l)
		with open(filename_EndData_l, "w", newline='\n') as fd_End_l:
			writer_End_l = csv.writer(fd_End_l)
			with open(filename_LoopData_r, "w", newline="\n") as fd_Loop_r:
				writer_Loop_r = csv.writer(fd_Loop_r)
		
				main(writer_Loop_l, writer_End_l, writer_Loop_r, Vicon_synch)





