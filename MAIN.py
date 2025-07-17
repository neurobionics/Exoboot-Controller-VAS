# Description:
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
#
# By: Nundini Rawal, John Hutchinson
# Date: 06/13/2024

import os, sys, time, threading, datetime

from flexsea.device import Device
from rtplot import client

from exoboot_thread import ExobootThread
from gait_state_estimation_thread import GaitStateEstimator
from grpc_thread import ExobootRemoteServerThread
from rtplotting_thread import rtPlottingThread

from src.logger.validator import Validator
from src.logger.logging_nexus import LoggingNexus
from src.logger.filing_cabinet import FilingCabinet
from src.utils.SoftRTloop import FlexibleSleeper
from src.utils.get_my_ip import get_ip_address
from src.settings.constants import *

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)


class MainControllerWrapper:
    """
    Runs Necessary threads on pi to run exoboot

    Allows for high level interaction with flexsea controller
    """

    def __init__(
        self,
        subjectID=None,
        trial_type=None,
        condition1=None,
        condition2=None,
        usebackup=False,
        continuousmode=False,
        overridedefaultcurrentbounds=False,
        main_loop_freq=0.2,
    ):
        self.main_loop_freq = main_loop_freq

        # Subject info
        self.subjectID = subjectID
        self.trial_type = trial_type
        self.condition1 = condition1["cond"]
        self.condition2 = condition2["cond"]
        self.usebackup = usebackup

        current_date = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMATTER_LESS_SEC)
        file_prefix_list = [arg for arg in [self.subjectID, self.trial_type, self.condition1, self.condition2] if arg]
        self.file_prefix = "_".join(file_prefix_list) + "_" + current_date
        print("DEBUG_fileprefix: ", self.file_prefix)

        # Exo alternative modes
        self.continuousmode = continuousmode
        self.overridedefaultcurrentbounds = overridedefaultcurrentbounds

        # Set up directories
        use_for_dir = [subjectID, trial_type]
        for cond in [condition1, condition2]:
            if cond["subdirectory"]:
                use_for_dir.append(cond["cond"])

        print("DEBUG_usefordir: ", *use_for_dir)

        # FilingCabinet
        self.filingcabinet = FilingCabinet(SUBJECT_DATA_PATH, *use_for_dir)
        if self.usebackup:
            loadstatus = self.filingcabinet.loadbackup(self.file_prefix, rule="newest")
            print(
                "Backup Load Status: {}".format("SUCCESS" if loadstatus else "FAILURE")
            )

        print("DEBUG_parentfolderpath", self.filingcabinet.getparentfolderpath())

        # OLD way that doesn't work: Get IP for GRPC server
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect(('10.255.255.255', 1))
        # self.myIP = s.getsockname()[0] + ":50055"

        # TODO: fix automatically getting ip address
        self.myIP = get_ip_address() + ":50055"
        print("myIP: {}".format(self.myIP))
        # self.myIP = "35.3.196.52" + ":50055"
        # print("myIP: {}".format(self.myIP))

    @staticmethod
    def get_active_ports():
        """
        To use the exos, it is necessary to define the ports they are going to be connected to.
        These are defined in the ports.yaml file in the flexsea repo
        """

        device_1 = Device(
            port=KNOWN_USB_SERIAL_PORTS[0], baud_rate=EXO_SETUP_CONST.BAUD_RATE
        )
        device_2 = Device(
            port=KNOWN_USB_SERIAL_PORTS[1], baud_rate=EXO_SETUP_CONST.BAUD_RATE
        )

        # Establish a connection between the computer and the device AND start streaming
        device_1.open(
            freq=EXO_SETUP_CONST.FLEXSEA_FREQ,
            log_level=EXO_SETUP_CONST.LOG_LEVEL,
            log_enabled=True,
        )
        device_2.open(
            freq=EXO_SETUP_CONST.FLEXSEA_FREQ,
            log_level=EXO_SETUP_CONST.LOG_LEVEL,
            log_enabled=True,
        )

        # Get side from side_dict
        side_1 = DEV_ID_TO_SIDE_DICT[device_1.dev_id]
        side_2 = DEV_ID_TO_SIDE_DICT[device_2.dev_id]

        print("Device 1: {}, {}".format(device_1.dev_id, side_1))
        print("Device 2: {}, {}".format(device_2.dev_id, side_2))

        # Always assign first pair of outputs to left side
        if side_1 == "left":
            return side_1, device_1, side_2, device_2
        elif side_1 == "right":
            return side_2, device_2, side_1, device_1
        else:
            raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")

    def run(self):
        """
        Initialize trial information
        Start All Threads
        """

        try:
            # Initializing the Exo
            side_left, device_left, side_right, device_right = self.get_active_ports()

            # Start device streaming and set gains:
            device_left.set_gains(
                DEFAULT_PID_GAINS.DEFAULT_KP,
                DEFAULT_PID_GAINS.DEFAULT_KI,
                DEFAULT_PID_GAINS.DEFAULT_KD,
                0,
                0,
                DEFAULT_PID_GAINS.DEFAULT_FF,
            )
            device_right.set_gains(
                DEFAULT_PID_GAINS.DEFAULT_KP,
                DEFAULT_PID_GAINS.DEFAULT_KI,
                DEFAULT_PID_GAINS.DEFAULT_KD,
                0,
                0,
                DEFAULT_PID_GAINS.DEFAULT_FF,
            )

            """Initialize Threads"""
            # Thread events
            self.quit_event = threading.Event()
            self.pause_event = threading.Event()
            self.log_event = threading.Event()
            self.quit_event.set()
            self.pause_event.clear()  # Start with threads paused
            self.log_event.clear()
            self.startstamp = TIME_METHOD()  # Timesync logging between all threads

            # Thread 1/2: Left and right exoboots
            self.exothread_left = ExobootThread(
                side=side_left,
                flexdevice=device_left,
                startstamp=self.startstamp,
                name="exothread_left",
                daemon=True,
                quit_event=self.quit_event,
                pause_event=self.pause_event,
                log_event=self.log_event,
                overridedefaultcurrentbounds=self.overridedefaultcurrentbounds,
                min_current=EXO_CURRENT_SAFETY_LIMITS.ZERO_CURRENT,
                max_current=EXO_CURRENT_SAFETY_LIMITS.MAX_ALLOWABLE_CURRENT,
                on_pause_triggers=0,  # TODO: wasn't being set to -1 earlier so just set it to 0
                threadfrequency=EXO_THREAD_FREQUENCIES.EXOTHREAD_FREQ,
            )

            self.exothread_right = ExobootThread(
                side=side_right,
                flexdevice=device_right,
                startstamp=self.startstamp,
                name="exothread_right",
                daemon=True,
                quit_event=self.quit_event,
                pause_event=self.pause_event,
                log_event=self.log_event,
                overridedefaultcurrentbounds=self.overridedefaultcurrentbounds,
                min_current=EXO_CURRENT_SAFETY_LIMITS.ZERO_CURRENT,
                max_current=EXO_CURRENT_SAFETY_LIMITS.MAX_ALLOWABLE_CURRENT,
                on_pause_triggers=0,
                threadfrequency=EXO_THREAD_FREQUENCIES.EXOTHREAD_FREQ,
            )

            self.exothread_left.start()
            self.exothread_right.start()

            # Thread 3: Gait State Estimator
            if GSE_MODE != "IMU":
                self.gse_thread = GaitStateEstimator(
                    startstamp=self.startstamp,
                    device_left=device_left,
                    device_right=device_right,
                    thread_left=self.exothread_left,
                    thread_right=self.exothread_right,
                    name="GSE",
                    filter_size=5,
                    daemon=True,
                    continuousmode=self.continuousmode,
                    quit_event=self.quit_event,
                    pause_event=self.pause_event,
                    log_event=self.log_event,
                )
                self.gse_thread.start()

            # Thread 4: Real-time plotting
            if RTPLOT_ENABLED:
                self.rtplot_thread = rtPlottingThread(
                    thread_left=self.exothread_left,
                    thread_right=self.exothread_right,
                    name="rtplot",
                    daemon=True,
                    quit_event=self.quit_event,
                    pause_event=self.pause_event
                )

            # Thread 5: Exoboot Remote Control
            self.remote_thread = ExobootRemoteServerThread(
                self,
                startstamp=self.startstamp,
                filingcabinet=self.filingcabinet,
                name="exoboot_remote_thread",
                usebackup=False,
                daemon=True,
                quit_event=self.quit_event,
                pause_event=self.pause_event,
                log_event=self.log_event,
            )
            self.remote_thread.set_target_IP(self.myIP)
            self.remote_thread.start()

            # LoggingNexus
            if GSE_MODE != "IMU":
                self.loggingnexus = LoggingNexus(
                    self.subjectID,
                    self.file_prefix,
                    self.filingcabinet,
                    self.exothread_left,
                    self.exothread_right,
                    self.gse_thread,
                )
            else:
                self.loggingnexus = LoggingNexus(
                    self.subjectID,
                    self.file_prefix,
                    self.filingcabinet,
                    self.exothread_left,
                    self.exothread_right,
                )

            # ~~~ Main Loop ~~~
            self.softrtloop = FlexibleSleeper(period=1 / self.main_loop_freq)

            while self.quit_event.is_set():
                try:
                    try:
                        print(
                            "Peak Torque Left/Right: ({}, {})".format(
                                self.loggingnexus.get(
                                    self.exothread_left.name, "peak_torque"
                                ),
                                self.loggingnexus.get(
                                    self.exothread_right.name, "peak_torque"
                                ),
                            )
                        )
                        print(
                            "Case Temp Left/Right: ({}, {})".format(
                                self.loggingnexus.get(
                                    self.exothread_left.name, "temperature"
                                ),
                                self.loggingnexus.get(
                                    self.exothread_right.name, "temperature"
                                ),
                            )
                        )
                        print(
                            "BattV Left/Right: ({}, {})\n".format(
                                self.loggingnexus.get(
                                    self.exothread_left.name, "battery_voltage"
                                ),
                                self.loggingnexus.get(
                                    self.exothread_right.name, "battery_voltage"
                                ),
                            )
                        )
                    except:
                        pass

                    # Log data. Obeys log_event
                    if self.log_event.is_set():
                        self.loggingnexus.log()

                    # SoftRT pause
                    self.softrtloop.pause()

                except KeyboardInterrupt:
                    print("Closing all threads")
                    self.quit_event.clear()

        except Exception as e:
            print("Exception: ", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            # Routine to close threads safely
            self.pause_event.set()
            time.sleep(0.25)
            self.quit_event.clear()

            # Stop motors and close device streams
            self.exothread_left.flexdevice.close()
            self.exothread_right.flexdevice.close()
            print("Goodbye")


if __name__ == "__main__":
    """
    Experiment Parameters
    """
    subjectID = "TESTER"
    trial_type = "vas"
    condition1 = {"cond": "session5", "subdirectory": True}
    condition2 = {"cond": "group4", "subdirectory": False}
    usebackup = "no"

    # Validate args
    # TODO: update validator
    # Validator(subjectID, trial_type, trial_cond, description, usebackup)
    condition1["cond"].upper()
    condition2["cond"].upper()

    # Set controller kwargs
    controller_kwargs = {
        "subjectID": subjectID,
        "trial_type": trial_type.upper(),
        "condition1": condition1,
        "condition2": condition2,
        "usebackup": usebackup in ["true", "True", "1", "yes", "Yes"],
    }

    # Allow GSE to alter peak torque during stride
    controller_kwargs["continuousmode"] = controller_kwargs[
        "trial_type"
    ] == "PREF" and controller_kwargs["condition1"] in ["SLIDER", "DIAL"]

    # Use alternate upper and lower current bounds
    controller_kwargs["overridedefaultcurrentbounds"] = controller_kwargs[
        "trial_type"
    ] == "VICKREY" and controller_kwargs["condition1"] in ["WNE", "NPO"]

    # Run the main controller
    MainControllerWrapper(**controller_kwargs).run()
