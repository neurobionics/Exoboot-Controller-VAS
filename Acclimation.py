# Description:
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
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
from rtplot import client 
import threading
import GUICommunicationThread

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

import config
import bertec_communication_thread
import Gait_State_EstimatorThread

from ExoClass import ExoObject
from SoftRTloop import FlexibleTimer
from utils import MovingAverageFilter


def get_active_ports(fxs):
	"""To use the exos, it is necessary to define the ports they are going to be connected to. 
	These are defined in the ports.yaml file in the flexsea repo.
 	"""
	port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
	ports, baud_rate = fxu.load_ports_from_file(port_cfg_path) # Flexsea api initialization

	# Always turn left exo on first for ports to line up or switch these numbers
	print("active ports recieved")
	dev_id_1 = fxs.open(ports[0], config.BAUD_RATE, log_level=3)
	dev_id_2 = fxs.open(ports[1], config.BAUD_RATE, log_level=3)

	print(dev_id_1, dev_id_2)

	if(dev_id_1 in config.LEFT_EXO_DEV_IDS):
		side_1  = 'left'
		side_2 = 'right'
	elif(dev_id_1 in config.RIGHT_EXO_DEV_IDS):
		side_1 = 'right' 
		side_2 = 'left'

	return side_1, dev_id_1, side_2, dev_id_2

class ExitMainLoopException(Exception):
    """Custom Exception to Exit out of the main VAS while loop """
    pass

def ACCLIMATION_MAIN(fxs, side_1, dev_id_1, side_2, dev_id_2, torque_settings, time_per_torque):
    
    try:
        # Instantiate exo object for both left and right sides
        if(side_1 == 'left'):
            exo_left = ExoObject(fxs, side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)
            exo_right = ExoObject(fxs, side=side_2, dev_id = dev_id_2,stream_freq=1000, data_log=False, debug_logging_level=3)
        else:
            exo_left = ExoObject(fxs, side=side_2, dev_id = dev_id_2, stream_freq=1000, data_log=False, debug_logging_level=3)
            exo_right = ExoObject(fxs, side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)

        input('Hit ANY KEY to allow belts to spool for BOTH exos')
		
  		# Command bias current to spool the belts
        exo_left.spool_belt()
        exo_right.spool_belt()
		
        input('Hit ANY KEY to START ZEROING procedure for BOTH exos')
  
        # Determine Motor & Ankle Encoder Offsets. Zero the exos every time you start this code
        exo_left.zeroProcedure()
        exo_right.zeroProcedure()
      
        input('Hit ANY KEY to send start ACTIVE commands to BOTH exos')
		
        # Set timing parameters from config
        input('Hit ANY KEY to send start ACTIVE commands to BOTH exos')
        exo_left.set_spline_timing_params(config.spline_timing_params)
        exo_right.set_spline_timing_params(config.spline_timing_params)

        # Iterate through your state machine controller that controls the exos
        input("Hit key to start acclimation")
        inProcedure = True
        while inProcedure:
            try:
                # every 10 strides (10 sec), increment the commanded torque
                for torque in torque_settings:
                    config.GUI_commanded_torque = torque
                    print("GUI_commanded_torque: ", config.GUI_commanded_torque)
                    
                    start_time = time()
                    while time() - start_time < time_per_torque:
                        # command exoskeleton state based on input from GUI 
                        exo_left.iterate()
                        exo_right.iterate()

                    print("Finished with: {}".format(torque))

                print("Acclimation Finished")

            except KeyboardInterrupt:
                print('Ctrl-C detected, Exiting Gracefully')
                exo_left.fxs.send_motor_command(exo_left.dev_id, fxe.FX_CURRENT, 0)
                exo_right.fxs.send_motor_command(exo_right.dev_id, fxe.FX_CURRENT, 0)
                sleep(0.5)

                exo_left.fxs.close(exo_left.dev_id)
                exo_right.fxs.close(exo_right.dev_id)
                break

            except Exception as err:
                print(traceback.print_exc())
                print("Unexpected error in executing inProcedure:", err)
                break
		
    except:
        print('EXCEPTION: Stopped')
        print("broke: ")
        print(traceback.format_exc())

    finally:
        # Stop the motors and close the device IDs before quitting
        exo_left.fxs.send_motor_command(exo_left.dev_id, fxe.FX_CURRENT, 0)
        exo_right.fxs.send_motor_command(exo_right.dev_id, fxe.FX_CURRENT, 0)
        sleep(0.5)

        exo_left.fxs.close(exo_left.dev_id)
        exo_right.fxs.close(exo_right.dev_id)

if __name__ == '__main__':
    try:
        config.trial_type = 'Acclimation'
        
        # Initialize the Exos
        fxs = flex.FlexSEA()
        side_1, dev_id_1, side_2, dev_id_2 = get_active_ports(fxs)
		
        print(side_1, dev_id_1, side_2, dev_id_2)

        fxs.start_streaming(dev_id_1, freq=1000, log_en=False)
        fxs.start_streaming(dev_id_2, freq=1000, log_en=False)
        fxs.set_gains(dev_id_1, config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)  
        fxs.set_gains(dev_id_2, config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)  

        # Starting the threads
        lock = threading.Lock()
        quit_event = threading.Event()
        quit_event.set()
  		
		# Thread:3 -- Gait State Estimator
        GSE = Gait_State_EstimatorThread.Gait_State_Estimator(fxs, dev_id_1, dev_id_2, quit_event=quit_event)
        GSE.daemon = True
        GSE.start()

        # Thread:4 -- Bertec Forceplate Streaming
        if config.bertec_fp_streaming:
            Bertec = bertec_communication_thread.Bertec(quit_event=quit_event)
            Bertec.daemon = True
            Bertec.start()
            print('Bertec Streaming started')
        
        # generate list of torques to iterate through        
        min_torque = 0.0
        max_torque = 30.0
        num_torque_settings = 12
        torque_step = (max_torque-min_torque)/num_torque_settings

        torque_settings = np.linspace(torque_step, max_torque, num_torque_settings, endpoint=True)
        print(torque_settings)

		# Main VAS state machine
        time_per_torque = 10 # s
        ACCLIMATION_MAIN(fxs, side_1, dev_id_1, side_2, dev_id_2, torque_settings, time_per_torque)

        # Joining the threads
        GSE.join()
        lock.acquire()
	
    except Exception as e:
        print("Exiting")
        print(e)
        quit_event.clear()