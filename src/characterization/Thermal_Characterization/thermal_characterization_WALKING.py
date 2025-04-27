# Description:
# Performs thermal test for walking uphill. Commands the exo using current control. 
# Uses gait state estimation informed by data streamed from the Bertec Forceplates.
# 
# Author: Nundini Rawal
# Date: 08/4/2024

import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np
from rtplot import client 
import threading
import bertec_communication_thread

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

# from ExoClass import ExoObject
from ExoClass_new import ExoObject
from src.utils.SoftRTloop import FlexibleTimer
from src.utils.utils import MovingAverageFilter

import config
import legacy.Gait_State_EstimatorThread as Gait_State_EstimatorThread

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

def thermal_walk_MAIN(fxs, side_1, dev_id_1, side_2, dev_id_2):
    try:
          # Instantiate exo object for both left and right sides
        if(side_1 == 'left'):
            exo_left = ExoObject(fxs, side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)
            exo_right = ExoObject(fxs, side=side_2, dev_id = dev_id_2,stream_freq=1000, data_log=False, debug_logging_level=3)
        else:
            exo_left = ExoObject(fxs, side=side_2, dev_id = dev_id_2, stream_freq=1000, data_log=False, debug_logging_level=3)
            exo_right = ExoObject(fxs, side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)

        # Command bias current to spool the belts
        input('Hit ANY KEY to allow belts to spool for BOTH exos')
        exo_left.spool_belt()
        exo_right.spool_belt()
        
        # Determine Motor & Ankle Encoder Offsets. Zero the exos every time you start this code
        input('Hit ANY KEY to START ZEROING procedure for BOTH exos')
        exo_left.zeroProcedure()
        exo_right.zeroProcedure()
      
        # Set timing parameters from config
        input('Hit ANY KEY to send start ACTIVE commands to BOTH exos')
        exo_left.set_spline_timing_params(config.spline_timing_params)
        exo_right.set_spline_timing_params(config.spline_timing_params)
    
        # Period Tracker
        period_tracker = MovingAverageFilter(size=300)
        prev_end_time = time()

        # Iterate through your state machine controller that controls the exos
        inProcedure = True
        while inProcedure:
            try:
                # command exoskeleton statte 
                exo_left.iterate()
                exo_right.iterate()
    
                if config.EXIT_MAIN_LOOP_FLAG:
                    raise ExitMainLoopException("Exit flag set, exiting main loop.")
                
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

            # Update Period Tracker and config
            end_time = time()
            period_tracker.update(end_time - prev_end_time)
            prev_end_time = end_time
            config.vas_main_frequency = 1/period_tracker.average()
        
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
        # ask user to input subject ID, trial number and presentation number
        config.subject_ID = input("Enter subject ID: ")
        config.trial_type = input("Enter trial type ( thermal_[INSERT CURRENT AMNT IN AMPS]):")

        print('Logging File SetUp Finished')
     
        # Initializing the Exo
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
        
        # Ask user for peak current to command:
        peak_current = input("Define a peak current amount (in mA): ")
        config.GUI_commanded_torque = float(peak_current)
    
        # Thread:3 -- Gait State Estimator
        GSE = Gait_State_EstimatorThread.Gait_State_Estimator(fxs, dev_id_1, dev_id_2, quit_event=quit_event)
        GSE.daemon = True
        GSE.start()
  
        if config.bertec_fp_streaming:
            # Thread:4 -- Bertec Forceplate Streaming
            Bertec = bertec_communication_thread.Bertec(quit_event=quit_event)
            Bertec.daemon = True
            Bertec.start()
            print('Bertec Streaming started')

        # Main VAS state machine
        thermal_walk_MAIN(fxs, side_1, dev_id_1, side_2, dev_id_2)

        # Joining the threads
        GSE.join()
        lock.acquire()
   
        if config.bertec_fp_streaming:
            Bertec.join()
            lock.acquire()
    
    except Exception as e:
        print("Exiting")
        print(e)
        quit_event.clear()
