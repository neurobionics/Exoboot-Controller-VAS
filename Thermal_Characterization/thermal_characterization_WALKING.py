# Description:
# Performs thermal test for walking uphill. Commands the exo using current control. 
# Uses gait state estimation informed by data streamed from the Bertec Forceplates.
# 
# Author: Nundini Rawal
# Date: 08/4/2024

# TODO: UPDATE EXOBOOT CALLS USING THE NEW FLEXSEA LIBRARY

import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np
from rtplot import client 
import threading
import GUICommunicationThread
import bertec_communication_thread

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea.device import Device

from ExoClass import ExoObject
from SoftRTloop import FlexibleTimer
from utils import MovingAverageFilter

import config
import Gait_State_EstimatorThread

def get_active_ports():
    """To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo.
     """
    # port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
    print("in get_active_ports")
    device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=6)
    device_2 = Device(port="/dev/ttyACM1", firmwareVersion="7.2.0", baudRate=230400, logLevel=6)
    
    # Establish a connection between the computer and the device    
    device_1.open()
    device_2.open()
    
    print("Dev1", device_1.id, device_1.connected)
    print("Dev2", device_2.id, device_2.connected)
    print("opened comm with device")
    
    if(device_1.id in config.LEFT_EXO_DEV_IDS):
        side_1  = 'left'
        side_2 = 'right'
    elif(device_1.id in config.RIGHT_EXO_DEV_IDS):
        side_1 = 'right' 
        side_2 = 'left'
    
    print("device connected and active ports recieved")

    return side_1, device_1, side_2, device_2

def validate_trial_type(trial_type):
    """Function to validate user entered trial type"""
    return trial_type in ["VAS", "Vickrey", "Acclimation"]

def validate_trial_presentation(trial_type, trial_presentation):
    """Function to validate trial presentation based on trial type"""
    if trial_type == "VAS":
        return trial_presentation.startswith("T") and "P" in trial_presentation
    elif trial_type == "Vickrey":
        return trial_presentation in ["NPO", "EPO", "WNE"]
    return False

class ExitMainLoopException(Exception):
    """Custom Exception to Exit out of the main VAS while loop """
    pass

def VAS_MAIN(side_1, device_1, side_2, device_2):
    try:
          # Instantiate exo object for both left and right sides
        if(side_1 == 'left'):
            exo_left = ExoObject(side = side_1, device = device_1)
            exo_right = ExoObject(side = side_2, device = device_2)
        else:
            exo_left = ExoObject(side=side_2, device = device_2)
            exo_right = ExoObject(side=side_1, device = device_1)

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
        period_tracker = MovingAverageFilter(initial_value=0, size=300)
        prev_end_time = time()

        # Iterate through your state machine controller that controls the exos
        inProcedure = True
        while inProcedure:
            try:
                # command exoskeleton state based on input from GUI 
                exo_left.iterate()
                exo_right.iterate()
    
                if config.EXIT_MAIN_LOOP_FLAG:
                    raise ExitMainLoopException("Exit flag set, exiting main loop.")
                
            except KeyboardInterrupt:
                print('Ctrl-C detected, Exiting Gracefully')
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
        exo_left.device.stop_motor() 
        exo_right.device.stop_motor()
        
        sleep(0.5)
        
if __name__ == '__main__':
    try:
        # ask user to input subject ID, trial number and presentation number
        config.subject_ID = input("Enter subject ID: ")
        config.trial_type = input("Enter trial type (VAS/Vickrey):")

        # Loop until valid trial type is entered
        while not validate_trial_type(config.trial_type):
            config.trial_type = input("Enter trial type (VAS/Vickrey): ")
            if not validate_trial_type(config.trial_type):
                print("Invalid trial type. Please try again.")

        # Enter valid trial presentation
        if config.trial_type == "VAS":
            config.trial_presentation = input("Enter trial # followed by presentation # (e.g. T1P2): ")
        elif config.trial_type == "Vickrey":
            config.trial_presentation = input("Enter NPO/EPO/WNE: ")
        if not validate_trial_presentation(config.trial_type, config.trial_presentation):
            print("Invalid trial presentation. Please exit and try again.")

        print('Logging File SetUp Finished')
     
        # Initializing the Exo
        # fxs = flex.FlexSEA()
        # side_1, dev_id_1, side_2, dev_id_2 = get_active_ports(fxs)
        side_1, device_1, side_2, device_2 = get_active_ports()
        print(side_1, device_1.id, side_2, device_2.id)
        
        # start device streaming and set gains:
        frequency = 1000
        device_1.start_streaming(frequency)
        device_2.start_streaming(frequency)
        device_1.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)
        device_2.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)

        # fxs.start_streaming(dev_id_1, freq=1000, log_en=False)
        # fxs.start_streaming(dev_id_2, freq=1000, log_en=False)
        # fxs.set_gains(dev_id_1, config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)  
        # fxs.set_gains(dev_id_2, config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)  

        # Starting the threads
        lock = threading.Lock()
        quit_event = threading.Event()
        quit_event.set()

        if config.trial_type == 'VAS':
            GUI = GUICommunicationThread.GUI_thread(quit_event=quit_event)    # Thread:2 -- GUI
            GUI.daemon = True
            GUI.start()
            print('GUI server started; run the GUI client on the Surface Tablet')
            input('Hit ANY KEY once the GUI client has been started')
        elif config.trial_type == 'Vickrey':
            config.GUI_commanded_torque = config.max_Vickrey_torque    # Fixed Commanded Torque (Nm) for the Vickrey trial
    
        # Thread:3 -- Gait State Estimator
        GSE = Gait_State_EstimatorThread.Gait_State_Estimator(side_1, device_1, side_2, device_2, quit_event=quit_event)
        GSE.daemon = True
        GSE.start()
  
        # Thread:4 -- Bertec Forceplate Streaming
        if config.bertec_fp_streaming:
            Bertec = bertec_communication_thread.Bertec(quit_event=quit_event)
            Bertec.daemon = True
            Bertec.start()
            print('Bertec Streaming started')

        # Main VAS state machine
        VAS_MAIN(side_1, device_1, side_2, device_2)

        # Joining the threads
        if config.trial_type == 'VAS':
            GUI.join()
            GSE.join()
            lock.acquire()
        elif config.trial_type == 'Vickrey':
            GSE.join()
            lock.acquire()
   
        if config.bertec_fp_streaming:
            Bertec.join()
            lock.acquire()
    
    except Exception as e:
        print("Exiting")
        print(e)
        quit_event.clear()


