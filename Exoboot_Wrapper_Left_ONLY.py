# Description: (USING 8.0.1 flexsea library - purposefully downgraded)
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
#
# Use with the following environment on the rpi: testing 
# To activate the environment use command: source testing/bin/activate.
# 
# Original template created by: Emily Bywater 
# Modified for VAS Vickrey protocol by: Nundini Rawal, John Hutchinson
# Date: 06/13/2024

import os, sys, csv, time, socket, threading

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

#from rtplot import client

from validator import Validator
from ExoClass_thread import ExobootThread
from GaitStateEstimator_thread_Left_ONLY import GaitStateEstimator
from exoboot_remote_control import ExobootRemoteServerThread
from LoggingClass import LoggingNexus, FilingCabinet
# from curses_HUD.hud_thread import HUDThread

from SoftRTloop import FlexibleSleeper
from constants import *

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

class MainControllerWrapper:
    """
    Runs Necessary threads on pi to run exoboot

    Allows for high level interaction with flexsea controller
    """
    def __init__(self, subjectID=None, trial_type=None, trial_cond=None, description=None, usebackup=False, continuousmode = False, overridedefaultcurrentbounds=False, streamingfrequency=FLEXSEA_AND_EXOTHREAD_FREQ, clockspeed=0.2):
        self.streamingfrequency = streamingfrequency
        self.clockspeed = clockspeed

        # Subject info
        self.subjectID = subjectID
        self.trial_type = trial_type
        self.trial_cond = trial_cond
        self.description = description
        self.usebackup = usebackup
        self.file_prefix = "{}_{}_{}_{}".format(self.subjectID, self.trial_type, self.trial_cond, self.description)

        # Exo alternative modes
        self.continuousmode = continuousmode
        self.overridedefaultcurrentbounds = overridedefaultcurrentbounds

        # FilingCabinet
        self.filingcabinet = FilingCabinet(SUBJECT_DATA_PATH, self.subjectID)
        if self.usebackup:
            loadstatus = self.filingcabinet.loadbackup(self.file_prefix, rule="newest")
            print("Backup Load Status: {}".format("SUCCESS" if loadstatus else "FAILURE"))

        # Get IP for GRPC server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        self.myIP = s.getsockname()[0] + ":50055"
        print("myIP: {}".format(self.myIP))
        
        self.fxs = flex.FlexSEA()
        print("asdf", self.fxs)

    def get_active_ports(self):
        """
        To use the exos, it is necessary to define the ports they are going to be connected to. 
        These are defined in the ports.yaml file in the flexsea repo
        """
        # port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'

        #ports, baud_rate = fxu.load_ports_from_file('/home/pi/VAS_exoboot_controller/ports.yaml')
        #print(ports, baud_rate)
        # device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)
        device_id_1 = self.fxs.open(port="/dev/ttyACM0", baud_rate=230400, log_level=3)
        print("Device ", device_id_1)


        # Get side from side_dict
        side_1 = DEV_ID_TO_SIDE_DICT[device_id_1]

        print("Device 1: {}, {}".format(device_id_1, side_1))
        # print("Device 2: {}, {}".format(device_2.id, side_2))

        # Always assign first pair of outputs to left side
        if side_1 == 'left':
            return side_1, device_id_1, None, None
        elif side_1 == 'right':
            return None, None, side_1, device_id_1
        else:
            raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")
    
    def run(self):
        """
        Initialize trial information
        Start All Threads
        """
        try:
            # Initializing the Exo
            side_left, device_id_left, side_right, device_id_right = self.get_active_ports()
            print(side_left, device_id_left, side_right, device_id_right)

            # Start device streaming and set gains:
            self.fxs.start_streaming(device_id_left, self.streamingfrequency, log_en = False)
            self.fxs.set_gains(device_id_left, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)

        #     """Initialize Threads"""
        #     # Thread events
        #     self.quit_event = threading.Event()
        #     self.pause_event = threading.Event()
        #     self.log_event = threading.Event()
        #     self.quit_event.set()
        #     self.pause_event.clear() # Start with threads paused
        #     self.log_event.clear()
        #     self.startstamp = time.perf_counter() # Timesync logging between all threads

        #     # Thread 1/2: Left and right exoboots
        #     self.exothread_left = ExobootThread(side_left, device_left, self.startstamp, "exothread_left", True, self.quit_event, self.pause_event, self.log_event, self.overridedefaultcurrentbounds, ZERO_CURRENT, MAX_ALLOWABLE_CURRENT, FLEXSEA_AND_EXOTHREAD_FREQ)
        #     self.exothread_left.start()

        #     # Thread 3: Gait State Estimator
        #     self.gse_thread = GaitStateEstimator(self.startstamp, device_left, self.exothread_left, filter_size=5, daemon=True, continuousmode=self.continuousmode, quit_event=self.quit_event, pause_event=self.pause_event, log_event=self.log_event)
        #     self.gse_thread.start()

        #     # Thread 4: Exoboot Remote Control
        #     self.remote_thread = ExobootRemoteServerThread(self, self.startstamp, self.filingcabinet, name='exoboot_remote_thread', usebackup=False, daemon=True, quit_event=self.quit_event, pause_event=self.pause_event, log_event=self.log_event)
        #     self.remote_thread.set_target_IP(self.myIP)
        #     self.remote_thread.start()

        #     # LoggingNexus
        #     self.loggingnexus = LoggingNexus(self.subjectID, self.file_prefix, self.filingcabinet, self.exothread_left, self.gse_thread)

        #     # ~~~Main Loop~~~
        #     self.softrtloop = FlexibleSleeper(period=1/self.clockspeed)
        #     # self.pause_event.set()
        #     # self.log_event.set()
        #     while self.quit_event.is_set():
        #         try:
        #             # Print if no hud
        #             try:
        #                 # if not self.hud.isrunning:
        #                 print("Peak Torque Left: {}".format(self.loggingnexus.get(self.exothread_left.name, "peak_torque")))
        #                 print("Case Temp Left: {}".format(self.loggingnexus.get(self.exothread_left.name, "temperature")))
        #                 print("BattV Left: {}\n".format(self.loggingnexus.get(self.exothread_left.name, "battery_voltage")))
        #             except:
        #                 pass

        #             # Log data. Obeys log_event
        #             if self.log_event.is_set():
        #                 self.loggingnexus.log()

        #             # SoftRT pause
        #             self.softrtloop.pause()

        #         except KeyboardInterrupt:
        #             print("Closing all threads")
        #             self.quit_event.clear()

        # except Exception as e:
        #     print("Exception: ", e)
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     print(exc_type, fname, exc_tb.tb_lineno)

        finally:            
            # Routine to close threads safely
            #zself.pause_event.set()
            time.sleep(0.25)
            #self.quit_event.clear()

            # Stop motors and close device streams
            self.exothread_left.flexdevice.stop_motor()

            self.exothread_left.flexdevice.close()
            print("Goodbye")


if __name__ == "__main__":
    assert len(sys.argv) - 1 == 5
    _, subjectID, trial_type, trial_cond, description, usebackup= sys.argv

    # Validate args
    Validator(subjectID, trial_type, trial_cond, description, usebackup)

    # Set controller kwargs
    controller_kwargs = {"subjectID": subjectID,
                         "trial_type": trial_type.upper(),
                         "trial_cond": trial_cond.upper(),
                         "description": description,
                         "usebackup": usebackup in ["true", "True", "1", "yes", "Yes"]}

    # Allow GSE to alter peak torque during strides
    controller_kwargs["continuousmode"] = controller_kwargs["trial_type"] == "PREF" and controller_kwargs["trial_cond"] in ["SLIDER", "DIAL"]

    # Use alternate upper and lower current bounds
    controller_kwargs["overridedefaultcurrentbounds"] = controller_kwargs["trial_type"] == "VICKREY" and controller_kwargs["trial_cond"] in ["WNE", "NPO"]

    MainControllerWrapper(**controller_kwargs).run()
