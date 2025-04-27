# Description:
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
# 
# Original template created by: Emily Bywater 
# Modified for VAS Vickrey protocol by: Nundini Rawal, John Hutchinson
# Date: 06/13/2024

import os, sys, csv, time, socket, threading

from flexsea.device import Device
#from rtplot import client

# from validator import Validator
# from ExoClass_thread import ExobootThread
# from GaitStateEstimator_thread_copy import GaitStateEstimator
# from exoboot_remote_control import ExobootRemoteServerThread
# from LoggingClass import LoggingNexus, FilingCabinet
# from curses_HUD.hud_thread import HUDThread

# from SoftRTloop import FlexibleSleeper
from constants import *

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

if __name__ == "__main__":
    device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)
    device_1.open()

    streamfreq = FLEXSEA_AND_EXOTHREAD_FREQ

    device_1.start_streaming(streamfreq)
    device_1.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)

    start_time = time.time()
    try:
        while True:
            data = device_1.read()
            print("elapsed, statetime: ({}, {})".format(data['state_time'] / 1000, time.time() - start_time))
            time.sleep(1/streamfreq)
    except:
        print("Exit")
        exit()
