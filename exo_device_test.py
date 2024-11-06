# Description:
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
# 
# Original template created by: Emily Bywater 
# Modified for VAS Vickrey protocol by: Nundini Rawal, John Hutchinson
# Date: 06/13/2024

import os, sys, csv, time, socket, threading

from flexsea.device import Device
from rtplot import client

from ExoClass_thread import ExobootThread
from LoggingClass import LoggingNexus, FilingCabinet
from GaitStateEstimator_thread import GaitStateEstimator
from exoboot_remote_control import ExobootRemoteServerThread
from curses_HUD.hud_thread import HUDThread

from SoftRTloop import FlexibleSleeper
from constants import DEV_ID_TO_SIDE_DICT, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_FF, RTPLOT_IP, TRIAL_CONDS_DICT

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "curses_HUD"))
from curses_HUD import hud_thread

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

class MainControllerWrapper:
    """
    Runs Necessary threads on pi to run exoboot

    Allows for high level interaction with flexsea controller
    """
    def __init__(self, subjectID, trial_type, trial_cond, description, streamingfrequency=1000, clockspeed=0.2):
        self.subjectID = subjectID
        self.trial_type = trial_type.upper()
        self.trial_cond = trial_cond.upper()
        self.description = description
        self.streamingfrequency = streamingfrequency
        self.clockspeed = clockspeed

        # Dummy mode check TODO implement dummymode
        if self.subjectID == "DUMMY":
            self.dummymode = True
        else:
            self.dummymode = False

        # Validate trial_type and trial_cond
        self.valid_trial_typeconds = TRIAL_CONDS_DICT
        try:
            if not self.trial_type in self.valid_trial_typeconds.keys():
                raise Exception("Invalid trial type: {} not in {}".format(self.trial_type, self.valid_trial_typeconds.keys()))

            valid_conds = self.valid_trial_typeconds[self.trial_type]
            if valid_conds and self.trial_cond not in valid_conds:
                raise Exception("Invalid trial cond: {} not in {}".format(trial_cond, valid_conds))
        except:
            print("\nINCORRECT ARGUMENTS\n")
            print("How to run: python Exoboot_Wrapper.py subjectID trial_type trial_cond description")
            print("See constants for all trial_type/trial_cond pairs")
        
        self.file_prefix = "{}_{}_{}_{}".format(self.subjectID, self.trial_type, self.trial_cond, self.description)

        # Get own IP address for GRPC
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        self.myIP = s.getsockname()[0] + ":50051"
        print("myIP: {}".format(self.myIP))

    @staticmethod
    def get_active_ports():
        """
        To use the exos, it is necessary to define the ports they are going to be connected to. 
        These are defined in the ports.yaml file in the flexsea repo
        """
        # port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
        # TODO remove explicit port references
        device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)
        device_2 = Device(port="/dev/ttyACM1", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)

        print(device_1.id)
        print(device_2.id)
        
        # Establish a connection between the computer and the device    
        device_1.open()
        device_2.open()

        # Get side from side_dict
        side_1 = DEV_ID_TO_SIDE_DICT[device_1.id]
        side_2 = DEV_ID_TO_SIDE_DICT[device_2.id]

        print("Device 1: {}, {}".format(device_1.id, side_1))
        print("Device 2: {}, {}".format(device_2.id, side_2))

        # Always assign first pair of outputs to left side
        if side_1 == 'left':
            return side_1, device_1, side_2, device_2
        elif side_1 == 'right':
            return side_2, device_2, side_1, device_1
        else:
            raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")
    
    def run(self):
        """
        Initialize trial information
        Start All Threads
        """
        # # Initializing the Exo
        side_left, device_left, side_right, device_right = self.get_active_ports()
        
        # # Start device streaming and set gains:
        device_left.start_streaming(self.streamingfrequency)
        device_right.start_streaming(self.streamingfrequency)
        device_left.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)
        device_right.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)
        print("Found Devices")

        time.sleep(0.5)

        print("Device Right")
        data_right = device_right.read()
        print(data_right, "\n")

        device_right.command_motor_current(-1 * 1000)

        input()

        print("Device Left")
        data_left = device_left.read()
        print(data_left)

        device_left.command_motor_current(-1 * 1000)

        input()

        print("Device Right")
        data_right = device_right.read()
        print(data_right, "\n")

        device_right.command_motor_current(-1 * 1000)

        input()

if __name__ == "__main__":
    _, subjectID, trial_type, trial_cond, description = sys.argv
    MainControllerWrapper(subjectID, trial_type, trial_cond, description, streamingfrequency=1000).run()
