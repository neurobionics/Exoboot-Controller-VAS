# Abstract Base class for threading
import threading
import queue

from typing import Type, Dict, Any, Optional
from abc import ABC, abstractmethod
from src.utils.flexible_sleeper import FlexibleSleeper
from non_singleton_logger import NonSingletonLogger
from dephyEB51 import DephyEB51Actuator

# logging setup
from src.utils.filing_utils import get_logging_info
from opensourceleg.logging import Logger, LogLevel
import logging


class BaseWorkerThread(threading.Thread, ABC):
    """
    Abstract base class for worker threads in the exoskeleton system.
    This class provides a template for creating threads that can be paused and quit.
    It includes methods for thread lifecycle management and a run method that
    handles the thread's main loop.
    """

    def __init__(
        self,
        quit_event: Type[threading.Event],
        pause_event: Type[threading.Event],
        log_event: Type[threading.Event],
        name: str,
        frequency: int = 100,
    ) -> None:

        super().__init__(name=name)
        self.quit_event = quit_event  # event to signal quitting
        self.pause_event = pause_event  # event to signal pausing
        self.log_event = log_event  # event to signal logging

        self.daemon = True
        self.frequency = int(frequency)
        self.rt_loop = FlexibleSleeper(
            dt=1 / frequency
        )  # create a soft real-time loop with the specified frequency

        # set-up a logger for each thread/instance
        logger_name = f"{name}_logger"
        log_path = "./src/logs/"
        self.data_logger = NonSingletonLogger(
            log_path=log_path,
            file_name=logger_name,
            file_level=logging.DEBUG,
            stream_level=logging.INFO,
            buffer_size=100,
        )

    def run(self) -> None:
        """
        Main loop structure for each instantiated thread.
        """
        LOGGER.debug(f"[{self.name}] Thread running.")

        while self.quit_event.is_set():  # while not quitting
            self.pre_iterate()  # run a pre-iterate method

            if not self.pause_event.is_set():
                self.on_pause()  # if paused, run once
            else:

                try:
                    self.iterate()  # call the iterate method to perform the thread's task
                except Exception as e:
                    LOGGER.debug(f"Exception in thread {self.name}: {e}")

            self.post_iterate()  # run a post-iterate method
            self.rt_loop.pause()

        # close logger instances before exiting threads
        self.data_logger.close()
        LOGGER.debug(f"[{self.name}] Thread exiting.")

    @abstractmethod
    def pre_iterate(self):
        """
        Override this abstract method in subclasses.
        This method is called BEFORE the iterate method.
        It can be used to perform any repetitive setup or initialization tasks.
        """
        LOGGER.debug(f"[{self.name}] pre-iterate() called.")
        pass

    @abstractmethod
    def iterate(self):
        """
        Override this abstract method in subclasses to do the thread's work.
        This method contains the main logic for the thread's operation.
        """
        LOGGER.debug(f"[{self.name}] iterate() called.")
        pass

    @abstractmethod
    def post_iterate(self):
        """
        Override this abstract method in subclasses.
        This method is called AFTER the iterate method.
        It can be used to perform any repetitive cleanup or logging, or finalization tasks.
        """
        LOGGER.debug(f"[{self.name}] post-iterate() called.")
        pass

    @abstractmethod
    def on_pause(self):
        """
        Override this abstract method in subclasses.
        Runs once before pausing threads.
        """
        LOGGER.debug(f"[{self.name}] on_pre_pause() called.")
        pass


from src.exo.assistance_calculator import AssistanceCalculator
from src.settings.constants import CONTINUOUS_MODE_FLAG, FLAT_WALK_TIMINGS, INCLINE_WALK_TIMINGS


class ActuatorThread(BaseWorkerThread):
    """
    Threading class for EACH actuator.
    This class handles the actuator's state updates and manages the actuator's control loop.
    """

    def __init__(
        self,
        name: str,
        actuator,
        msg_router,
        quit_event: Type[threading.Event],
        pause_event: Type[threading.Event],
        log_event: Type[threading.Event],
        frequency: int = 100,
    ) -> None:

        super().__init__(quit_event, pause_event, log_event, name, frequency=frequency)

        self.actuator = actuator
        self.actuator.start()  # start actuator

        self.msg_router = msg_router
        self.inbox = None

        # instantiate assistance generator
        self.assistance_calculator = AssistanceCalculator(
            t_rise=INCLINE_WALK_TIMINGS.P_RISE,
            t_peak=INCLINE_WALK_TIMINGS.P_PEAK,
            t_fall=INCLINE_WALK_TIMINGS.P_FALL,
        )

        # set-up vars:
        self.HS_time: float = 0.0
        self.stride_period: float = 1.2
        self.in_swing: bool = True
        self.peak_torque_setpoint: float = 0.0
        self.torque_command: float = 0.0
        self.current_setpoint: int = 0
        self.time_in_stride: float = 0.0

        self.thread_start_time: float = time.perf_counter()
        self.time_since_start: float = 0.0

        # track vars for csv logging
        self.data_logger.track_variable(
            lambda: self.time_since_start, "time_since_start"
        )
        self.data_logger.track_variable(lambda: self.HS_time, "HS_time")
        self.data_logger.track_variable(lambda: self.stride_period, "stride_period")
        self.data_logger.track_variable(lambda: self.in_swing, "in_swing_flag_bool")
        self.data_logger.track_variable(
            lambda: self.peak_torque_setpoint, "peak_torque_setpt"
        )
        self.data_logger.track_variable(lambda: self.torque_command, "torque_command")
        self.data_logger.track_variable(
            lambda: self.current_setpoint, "current_setpoint"
        )
        # track gse_imu vars
        self.data_logger.track_variable(lambda: self.actuator.imu_gait_state_estimate("HS_time"), "HS_time_imu")
        self.data_logger.track_variable(lambda: self.actuator.imu_gait_state_estimate("stride_period"), "stride_period_imu")
        self.data_logger.track_variable(lambda: self.actuator.imu_gait_state_estimate("in_swing"), "in_swing_imu")
        # self.data_logger.track_variable(lambda: self.actuator.ankle_angle, "ank_ang")
        # self.data_logger.track_variable(lambda: self.actuator.gear_ratio, "gear_ratio")

    def pre_iterate(self) -> None:
        """
        Check inbox for messages from GSE & GUI threads
        """

        mail_list = self.inbox.get_all_mail()
        for mail in mail_list:
            self.decode_message(mail)

    def decode_message(self, mail):
        """
        Decode a message from the inbox.
        This method extracts the contents of the message and updates the actuator's state accordingly.
        """
        try:
            for key, value in mail.contents.items():
                if CONTINUOUS_MODE_FLAG and key == "peak_torque_setpoint":
                    self.peak_torque_update_monitor(key, value)
                else:
                    setattr(self, key, value)

        except Exception as err:
            self.data_logger.debug(f"Error decoding message: {err}")

    def peak_torque_update_monitor(self, key, value):
        """
        This method monitors changes in the peak torque setpoint from the GUI thread
        and ensures that a new setpoint is shared ONLY if the user is in swing-phase

        This is to prevent the current command from being altered mid-stride.
        A new torque will only be felt upon the termination of the current stride.
        """
        # TODO: add in more logic to handle continous vs discrete modes (GUI doesn't send continous stream of data)

        if self.in_swing:
            setattr(self, key, value)

    def iterate(self) -> None:
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """

        self.time_since_start = time.perf_counter() - self.thread_start_time
        self.actuator.update()      # update actuator states
        self.data_logger.update()   # update logger

        # IMU OVERRIDE
        # try:
        #     # full_dict = self.actuator.imu_gait_state_estimate()
        #     self.HS_time = self.actuator.imu_gait_state_estimate("HS_time")
        #     self.stride_period = self.actuator.imu_gait_state_estimate("stride_period")
        #     self.in_swing = self.actuator.imu_gait_state_estimate("in_swing")
        # except Exception as e:
        #     LOGGER.error(f"Ur dumb: {e}")

        # obtain time in current stride
        self.time_in_stride = time.perf_counter() - self.HS_time
        LOGGER.debug(f"boo {self.name}{self.actuator.ankle_angle} {self.actuator.gear_ratio}")

        # TODO add delay compensation

        # acquire torque command based on gait estimate
        self.torque_command = self.assistance_calculator.torque_generator(
            current_time=self.time_in_stride,
            stride_period=self.stride_period,
            peak_torque=float(self.peak_torque_setpoint),
            in_swing=self.in_swing,
        )

        # determine appropriate current setpoint that matches the torque setpoint
        self.current_setpoint = self.actuator.torque_to_current(self.torque_command)

        # command appropriate current setpoint using DephyExoboots class
        if self.current_setpoint is not None:
            # self.actuator.set_motor_current(self.current_setpoint)
            pass
        else:
            self.data_logger.warning(
                f"Unable to command current for {self.actuator.tag}. Skipping."
            )

    def post_iterate(self) -> None:
        # send data to main thread for rtplotting
        try:
            msg_router.send(
                sender=self.name,
                recipient="main",
                contents={
                    # "time_since_start": self.time_since_start,
                    "peak_torque_setpoint": self.peak_torque_setpoint,
                    "torque_command": self.torque_command,
                    "current_setpoint": self.current_setpoint,
                    "motor_current": self.actuator.motor_current,
                    "activation_status": self.actuator.imu_gait_state_estimate("in_swing")
                },
            )

        except:
            self.data_logger.debug(
                f"UNABLE TO SEND msg to MAIN from {self.name} thread. Skipping."
            )

        # TODO add rest of stuff
        if self.log_event.is_set():
            self.data_logger.debug(f"[{self.name}] log_event True")

    def on_pause(self) -> None:
        pass


from gse_bertec import Bertec_Estimator
from src.exo.gait_state_estimator.forceplate.ZMQ_PubSub import Subscriber
from src.settings.constants import IP_ADDRESSES, USE_SIMULATED_WALKER


class GaitStateEstimatorThread(BaseWorkerThread):
    """
    Threading class for the Gait State Estimator.
    This class handles gait state estimation for BOTH exoskeletons/sides together.
    """

    def __init__(
        self,
        msg_router,
        quit_event: Type[threading.Event],
        pause_event: Type[threading.Event],
        log_event: Type[threading.Event],
        active_actuators: list[str],
        name: Optional[str] = None,
        frequency: int = 100,
    ) -> None:

        super().__init__(
            quit_event, pause_event, log_event, name=name, frequency=frequency
        )

        self.msg_router = msg_router
        self.inbox = None  # will be instantiated

        self.active_actuators = active_actuators
        self.bertec_estimators = {}

        self.time_since_start = 0
        self.thread_start_time = time.perf_counter()

        # for each active actuator, initialize GSE Bertec
        for actuator in self.active_actuators:
            selected_topic = f"fz_{actuator}"  # e.g., 'fz_left' or 'fz_right'

            # if USE_SIMULATED_WALKER:
            #     walker = WalkingSimulator(stride_period=1.20)
            #     walker.set_percent_toe_off(67)
            #     self.bertec_estimators[actuator] = walker

            #     # track vars for csv logging
            #     self.data_logger.track_variable(
            #         lambda: self.time_since_start, f"{actuator}_time_since_start"
            #     )
            #     self.data_logger.track_variable(
            #         lambda: self.bertec_estimators[actuator].stride_start_time,
            #         f"{actuator}_HS_time_",
            #     )
            #     self.data_logger.track_variable(
            #         lambda: self.bertec_estimators[actuator].stride_period,
            #         f"{actuator}_stride_period",
            #     )
            #     self.data_logger.track_variable(
            #         lambda: self.bertec_estimators[actuator].in_swing_flag,
            #         f"{actuator}_in_swing_flag_bool",
            #     )
            #     self.data_logger.track_variable(
            #         lambda: self.bertec_estimators[actuator].current_time_in_stride,
            #         f"{actuator}_current_time_in_stride",
            #     )
            #     self.data_logger.track_variable(
            #         lambda: self.bertec_estimators[actuator].current_percent_gait_cycle,
            #         f"{actuator}_current_percent_gait_cycle",
            #     )

            # else:
            bertec_subscriber = Subscriber(
                publisher_ip=IP_ADDRESSES.VICON_IP,
                topic_filter=selected_topic,
                timeout_ms=5,
            )
            self.bertec_estimators[actuator] = Bertec_Estimator(
                zmq_subscriber=bertec_subscriber
            )

                # # track vars for csv logging
                # self.data_logger.track_variable(
                #     lambda: self.time_since_start, f"{actuator}_time_since_start"
                # )
                # self.data_logger.track_variable(
                #     lambda: self.bertec_estimators[actuator].HS,
                #     f"{actuator}_HS_time_",
                # )
                # self.data_logger.track_variable(
                #     lambda: self.bertec_estimators[actuator].stride_period_tracker.average(),
                #     f"{actuator}_stride_period",
                # )
                # self.data_logger.track_variable(
                #     lambda: not self.bertec_estimators[actuator].in_contact,
                #     f"{actuator}_in_swing_flag_bool",
                # )

    def pre_iterate(self) -> None:
        pass


    def iterate(self):
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.

        It updates the gait state estimator and sends the current time in stride and stride period to the actuators.
        """
        self.time_since_start = time.perf_counter() - self.thread_start_time

        # for each active actuator,
        for actuator in self.active_actuators:

            # Update the gait state estimator for the actuator
            self.bertec_estimators[actuator].update()
            print(f"asdf {actuator}: {self.bertec_estimators[actuator].return_estimate()}")

            # update csv logger
            self.data_logger.update()

            # send message to actuator inboxes
            try:
                self.data_logger.debug(
                    self.bertec_estimators[actuator].return_estimate()
                )

                msg_router.send(
                    sender=self.name,
                    recipient=actuator,
                    contents=self.bertec_estimators[actuator].return_estimate(),
                )
            except:
                self.data_logger.debug(
                    f"UNABLE TO SEND msg to '{actuator}' actuator from GaitStateEstimatorThread. Skipping."
                )
                continue

    def post_iterate(self) -> None:
        pass

    def on_pause(self) -> None:
        pass


import sys
import select
import random


class GUICommunication(BaseWorkerThread):
    """
    Threading class to simulate GUI communication via gRPC.
    This class handles GUI communication for BOTH exoskeletons/sides together.

    It constantly monitors for new user input specifying a desired torque setpoint.
    It then sends these setpoints to the actuators to handle.
    """

    def __init__(
        self,
        msg_router,
        quit_event: Type[threading.Event],
        pause_event: Type[threading.Event],
        log_event: Type[threading.Event],
        active_actuators: list[str],
        name: Optional[str] = None,
        frequency: int = 100,
    ) -> None:

        super().__init__(
            quit_event, pause_event, log_event, name=name, frequency=frequency
        )

        self.msg_router = msg_router
        self.inbox = None
        self.active_actuators = active_actuators
        self.peak_torque_setpoint: float = 0.0

        self.thread_start_time: float = time.perf_counter()
        self.time_since_start: float = 0.0

        # track vars for csv logging
        self.data_logger.track_variable(lambda: self.peak_torque_setpoint, "torque_setpt")

    def pre_iterate(self) -> None:
        """
        Pre-iterate method to check for new messages in the mailbox.
        """
        pass

    def iterate(self):
        """
        Non-blocking: Only read user input if available.
        Allow user to input a new desired torque setpoint.
        If the user doesn't input a new value, the current setpoint is used.
        """

        self.time_since_start = time.perf_counter() - self.thread_start_time

        # update csv logging
        self.data_logger.update()

        # set a random torque setpoint
        self.peak_torque_setpoint = 15.0 #random.randint(2,4)*10

        for actuator in self.active_actuators:
            try:
                msg_router.send(
                    sender=self.name,
                    recipient=actuator,
                    contents={"peak_torque_setpoint": self.peak_torque_setpoint},
                )
            except:
                self.data_logger.debug(
                    f"UNABLE TO SEND msg to actuator from GUICommunication thread. Skipping."
                )

    def post_iterate(self) -> None:
        pass

    def on_pause(self) -> None:
        pass


from dephyEB51 import DephyEB51Actuator
from opensourceleg.logging import LOGGER
from src.settings.constants import RUN_BERTEC_GSE
from typing import Union, Dict
import time


class ThreadManager:
    """
    This class manages thread creation, communication and termination for the exoskeleton system.
    """

    def __init__(self, msg_router, actuators: Dict) -> None:

        self.actuators = actuators  # Dictionary of Actuators
        self.msg_router = msg_router  # MessageRouter class instance

        # create threading events common to all threads
        self._quit_event = threading.Event()  # Event to signal threads to quit.
        self._pause_event = threading.Event()  # Event to signal threads to pause.
        self._log_event = threading.Event()  # Event to signal threads to log

        # initialize thread events
        self._quit_event.set()  # exo is running
        self._pause_event.clear()  # exo starts paused
        self._log_event.clear()  # exo starts not logging

        # initialize dict of threads
        self._threads = {}

    def start(self) -> None:
        """
        Creates the following threads:
         - for each ACTIVE actuator
         - for the Gait State Estimator (ONLY IF THE RUN_BERTEC_GSE_FLAG = True)
         - for the GUI
        """

        for actuator in self.actuators.values():
            self.initialize_actuator_thread(actuator)

        # creating 1 thread for the Gait State Estimator
        if RUN_BERTEC_GSE == True:
            self.initialize_GSE_thread(active_actuators=self.actuators.keys())

        # creating 1 thread for GUI communication
        self.initialize_GUI_thread(active_actuators=self.actuators.keys())

    def start_all_threads(self) -> None:
        """
        Start all threads in the thread manager.
        This method is called to start all threads after they have been initialized.
        """

        for thread in self._threads.values():
            thread.start()
            LOGGER.debug(f"Thread {thread.name} started.")

    def stop(self) -> None:
        """Signal threads to quit and join them"""

        # clearing the quit event so all threads recieve the kill signal
        self._quit_event.clear()
        LOGGER.debug("Setting quit event for all threads.")

        # ensure that both actuators are properly shut down
        for actuator in self.actuators.values():
            LOGGER.debug(f"Calling stop method of {actuator.tag}")
            actuator.stop()

        # ensure time to enact stop method before moving on
        time.sleep(0.2)

    def initialize_actuator_thread(self, actuator: DephyEB51Actuator) -> None:
        """
        Create and start a thread for the specified actuator.
        This method is called to set up the actuator communication thread.
        """

        actuator_thread = ActuatorThread(
            actuator=actuator,
            quit_event=self._quit_event,
            pause_event=self._pause_event,
            log_event=self._log_event,
            name=f"{actuator.side}",
            frequency=500,
            msg_router=self.msg_router,
        )

        LOGGER.debug(f"created {actuator.side} actuator thread")
        self._threads[actuator.side] = actuator_thread

    def initialize_GSE_thread(self, active_actuators: list[str]) -> None:
        """
        Create and start the Gait State Estimator thread.
        This method is called to set up the GSE communication thread.

        Args:
            active_actuators: List of active actuators to be monitored by the GSE.
                                This is used to initialize the Gait State Estimator.
        """
        # create a FIFO queue with max size for inter-thread communication
        name = "gse"
        gse_thread = GaitStateEstimatorThread(
            quit_event=self._quit_event,
            pause_event=self._pause_event,
            log_event=self._log_event,
            active_actuators=active_actuators,
            name=name,
            frequency=250,
            msg_router=self.msg_router,
        )

        LOGGER.debug(f"created gse thread")
        self._threads[name] = gse_thread

    def initialize_GUI_thread(self, active_actuators: list[str]) -> None:
        """
        Create and start the GUI thread for user input.
        This method is called to set up the GUI communication thread.
        """

        # create a FIFO queue with max size for inter-thread communication
        name = "gui"
        gui_thread = GUICommunication(
            quit_event=self._quit_event,
            pause_event=self._pause_event,
            log_event=self._log_event,
            active_actuators=active_actuators,
            name=name,
            frequency=1,
            msg_router=self.msg_router,
        )
        LOGGER.debug(f"created gui thread")
        self._threads[name] = gui_thread

    def return_active_threads(self) -> list:
        """
        Return list of active thread addresses.
        """
        return self._threads.values()

    def __enter__(self) -> None:
        """
        Context manager enter method.
        This method is called when the ThreadManager is used in a with statement.
        """
        self.start()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Context manager exit method.
        This method is called when the ThreadManager is used in a with statement.
        It stops all threads and cleans up.
        """
        self.stop()

    @property
    def left_exo_queue(self) -> Union[None, queue.Queue]:
        """Get the queue for the left actuator"""
        thread = self._threads.get("left")

        if hasattr(thread, "inbox"):
            return thread.inbox
        else:
            LOGGER.error("Left actuator thread has no attribute inbox")
            return None

    @property
    def right_exo_queue(self) -> Union[None, queue.Queue]:
        """Get the queue for the right actuator"""
        thread = self._threads.get("right")

        if hasattr(thread, "inbox"):
            return thread.inbox
        else:
            LOGGER.error("Right actuator thread has no attribute inbox")
            return None

    @property
    def gse_queue(self) -> Union[None, queue.Queue]:
        """Get the queue for the gait state estimator"""
        thread = self._threads.get("gse")

        if hasattr(thread, "inbox"):
            return thread.inbox
        else:
            LOGGER.error("GSE thread has no attribute inbox")
            return None

    @property
    def gui_queue(self) -> Union[None, queue.Queue]:
        """Get the queue for the GUI communication"""
        thread = self._threads.get("gui")

        if hasattr(thread, "inbox"):
            return thread.inbox
        else:
            LOGGER.error("GUI thread has no attribute inbox")
            return None

    @property
    def left_thread(self) -> Optional[ActuatorThread]:
        """Get the left actuator thread"""
        return self._threads.get("left")

    @property
    def right_thread(self) -> Optional[ActuatorThread]:
        """Get the right actuator thread"""
        return self._threads.get("right")

    @property
    def gse_thread(self) -> Optional[ActuatorThread]:
        """Get the right actuator thread"""
        return self._threads.get("gse")

    @property
    def gui_thread(self) -> Optional[ActuatorThread]:
        """Get the right actuator thread"""
        return self._threads.get("gui")


class MainThreadMessageReception:

    def __init__(self, actuators):
        """
        Main thread named and set-up.

        Args:
            - actuators(DephyEB51): dictonary of actuator objects
        """

        self.name = "main"
        self.inbox = None
        self.actuators = actuators

        # define list of vars to be recepted
        recepted_vars = ["peak_torque_setpoint",
                         "torque_command",
                         "current_setpoint",
                         "motor_current",
                         "activation_status"
                         ]

        # loop through actuator names & assign vars as attributes of class
        for actuator in self.actuators.keys():
            for var in recepted_vars:
                setattr(self, f"{actuator}_{var}", 0)

    def check_msg_inbox(self):
        """
        Main thread checks it's message inbox.
        """
        mail_list = self.inbox.get_all_mail()
        for mail in mail_list:
            self.decode_message(mail)

    def decode_message(self, mail):
        """
        Decode a message from the inbox.
        This method extracts the contents of the message and updates the class states accordingly.

        Args:
            Mail: mail object
        """

        try:
            sender = mail.sender  # i.e., "left" or "right"
            for key, value in mail.contents.items():
                # e.g. store as left_peak_torque_setpoint or right_peak_torque_setpoint
                if key == "current_setpoint":
                    setattr(self, f"{sender}_{key}", value/1000)
                else:
                    setattr(self, f"{sender}_{key}", value)

        except Exception as err:
            LOGGER.debug(f"Error decoding message: {err}")

    def initialize_rt_plots(self) -> list:
        """
        Initialize real-time plots.

        """
        # converting actuator dictionary keys to a list
        active_sides_list = list(self.actuators.keys())

        print("Active actuators:", active_sides_list)

        # pre-slice colors based on the number of active actuators
        colors = ["r", "b"][: len(active_sides_list)]
        if len(active_sides_list) > len(colors):
            raise ValueError(
                "Not enough unique colors for the number of active actuators."
            )

        # repeat line styles and widths for each active actuator
        line_styles = ["-" for _ in active_sides_list]
        line_widths = [2 for _ in active_sides_list]

        torque_setpt_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Exo Torque Setpt (Nm) vs. Sample",
            "ylabel": "Torque (Nm)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 45],
        }

        torque_cmd_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Exo Torque Cmds (A) vs. Sample",
            "ylabel": "Torque (Nm)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 45],
        }

        current_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Exo Current (A) vs. Sample",
            "ylabel": "Current (A)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 30],
        }

        mot_current_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Exo Motor Current (A) vs. Sample",
            "ylabel": "Motor Current (A)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 30],
        }

        activation_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Activation vs. Sample",
            "ylabel": "Gait Event Activation",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 1],
        }


        plot_config = [torque_setpt_plt_config,
                       torque_cmd_plt_config,
                       current_plt_config,
                       mot_current_plt_config,
                       activation_plt_config]

        return plot_config

    def update_rt_plots(self) -> list:
        """
        Updates the real-time plots with current values for:

        Returns:
            plot_data_array: A list of data arrays (for active actuators) for each plot.
        """

        data_to_plt = []

        # looping through actuator names, plot data that is sent from actuator thread
        # does not contain actual motor currents in response to commands (just what's commanded)
        for actuator in self.actuators.keys():
            data_to_plt.append(getattr(self, f"{actuator}_peak_torque_setpoint"))

        for actuator in self.actuators.keys():
            data_to_plt.append(getattr(self, f"{actuator}_torque_command"))

        for actuator in self.actuators.keys():
            data_to_plt.append(abs(getattr(self, f"{actuator}_current_setpoint")))

        for actuator in self.actuators.keys():
            data_to_plt.append(abs(getattr(self, f"{actuator}_motor_current")))

        for actuator in self.actuators.keys():
            data_to_plt.append(abs(getattr(self, f"{actuator}_activation_status")))

        return data_to_plt


# Example main loop
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils.actuator_utils import create_actuators
from src.settings.constants import EXO_SETUP_CONST
from src.utils.walking_simulator import WalkingSimulator
from exoboot_messenger_hub import MessageRouter
from rtplot import client
from exoboots import DephyExoboots

if __name__ == "__main__":
    # import time
    # time1 = time.perf_counter()
    # time2 = time.time()

    # print("blah: ", time1 - time2)
    # time.sleep(10)

    # create actuators & Exoboots Robot
    actuators = create_actuators(
        gear_ratio=1,
        baud_rate=EXO_SETUP_CONST.BAUD_RATE,
        freq=EXO_SETUP_CONST.FLEXSEA_FREQ,
        debug_level=EXO_SETUP_CONST.LOG_LEVEL,
    )

    exoboots = DephyExoboots(tag="exoboots", actuators=actuators, sensors={})

    # set actuator modes & spool belts
    exoboots.setup_control_modes()
    # exoboots.spool_belts()

    # initialize class responsible for recieving data & rtplotting for the main thread
    main_thread_receptor = MainThreadMessageReception(actuators)

    # initalize rtplotting
    client.configure_ip(IP_ADDRESSES.RTPLOT_IP)
    plot_config = main_thread_receptor.initialize_rt_plots()
    client.initialize_plots(plot_config)

    # create a message router for inter-thread communication
    msg_router = MessageRouter()

    # instantiate thread manager
    system_manager = ThreadManager(msg_router=msg_router, actuators=actuators)

    # instantiate soft real-time clock
    clock = SoftRealtimeLoop(dt=1 / 200)  # Hz

    with system_manager:
        # set-up addressbook for the PostOffice & create inboxes for each thread
        msg_router.setup_addressbook(
            *system_manager.return_active_threads(), main_thread_receptor
        )

        # start all threads
        system_manager.start_all_threads()

        # unpause exos (removed "not" from base thread for this to work)
        system_manager._pause_event.set()

        for t in clock:
            try:
                # decode messages from actuator threads
                main_thread_receptor.check_msg_inbox()

                # send data to server & update real-time plots
                data_to_plt = main_thread_receptor.update_rt_plots()
                client.send_array(data_to_plt)

            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break
