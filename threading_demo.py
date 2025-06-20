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

    def __init__(self,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 log_event:Type[threading.Event],
                 name:str,
                 frequency:int=100)->None:

        super().__init__(name=name)
        self.quit_event = quit_event    # event to signal quitting
        self.pause_event = pause_event  # event to signal pausing
        self.log_event = log_event      # event to signal logging

        self.daemon = True
        self.frequency = int(frequency)
        self.rt_loop = FlexibleSleeper(dt=1/frequency)  # create a soft real-time loop with the specified frequency

        # set-up a logger for each thread/instance
        logger_name = f"{name}_logger"
        log_path = "./src/logs/"
        self.data_logger = NonSingletonLogger(
            log_path=log_path,
            file_name=logger_name,
            file_level=logging.DEBUG,
            stream_level=logging.INFO,
            buffer_size=100
        )

    def run(self)->None:
        """
        Main loop structure for each instantiated thread.
        """
        LOGGER.debug(f"[{self.name}] Thread running.")

        while self.quit_event.is_set():     # while not quitting
            self.pre_iterate()              # run a pre-iterate method

            if not self.pause_event.is_set():
                self.on_pause()             # if paused, run once
            else:

                try:
                    self.iterate()          # call the iterate method to perform the thread's task
                except Exception as e:
                    LOGGER.debug(f"Exception in thread {self.name}: {e}")

            self.post_iterate()             # run a post-iterate method
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

class ActuatorThread(BaseWorkerThread):
    """
    Threading class for EACH actuator.
    This class handles the actuator's state updates and manages the actuator's control loop.
    """

    def __init__(self,
                 name: str,
                 actuator,
                 msg_router,
                 quit_event: Type[threading.Event],
                 pause_event: Type[threading.Event],
                 log_event: Type[threading.Event],
                 frequency: int = 100) -> None:

        super().__init__(quit_event, pause_event, log_event, name, frequency=frequency)

        self.actuator = actuator
        self.actuator.start()   # start actuator

        self.msg_router = msg_router
        self.inbox = None

        # instantiate assistance generator
        self.assistance_calculator = AssistanceCalculator()

        # set-up vars:
        self.HS_time:float = 0.0
        self.stride_period:float = 1.2
        self.in_swing:bool = True
        self.torque_setpoint:float = 0.0
        self.torque_command:float = 0.0
        self.current_setpoint:int = 0

        self.thread_start_time:float = time.perf_counter()
        self.time_since_start:float = 0.0

        # track vars for csv logging
        self.data_logger.track_variable(lambda: self.time_since_start, "time_since_start")
        self.data_logger.track_variable(lambda: self.HS_time, "HS_time")
        self.data_logger.track_variable(lambda: self.stride_period, "stride_period")
        self.data_logger.track_variable(lambda: self.in_swing, "in_swing_flag_bool")
        self.data_logger.track_variable(lambda: self.torque_setpoint, "peak_torque_setpt")
        self.data_logger.track_variable(lambda: self.torque_command, "torque_cmd")
        self.data_logger.track_variable(lambda: self.current_setpoint, "current_setpoint")

    def pre_iterate(self)->None:
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
                # TODO: value validation (not None or something)

                if key == "torque_setpoint":
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

        if self.in_swing:
            setattr(self, key, value)

    def iterate(self)->None:
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """

        self.time_since_start = time.perf_counter() - self.thread_start_time
        self.actuator.update()
        self.data_logger.update()   # update logger

        # obtain time in current stride
        self.time_in_stride = time.perf_counter() - self.HS_time

        # acquire torque command based on gait estimate
        self.torque_command = self.assistance_calculator.torque_generator(self.time_in_stride,
                                                                     self.stride_period,
                                                                     float(self.torque_setpoint),
                                                                     self.in_swing)

        # determine appropriate current setpoint that matches the torque setpoint
        self.current_setpoint = self.actuator.torque_to_current(self.torque_command)

        # command appropriate current setpoint using DephyExoboots class
        if self.current_setpoint is not None:
            # self.actuator.set_motor_current(current_setpoint)
            pass
        else:
            self.data_logger.warning(f"Unable to command current for {self.actuator.tag}. Skipping.")

    def post_iterate(self)->None:
        # TODO add rest of stuff
        if self.log_event.is_set():
            self.data_logger.debug(f"[{self.name}] log_event True")

    def on_pause(self)->None:
        pass



from gse_bertec import Bertec_Estimator
from src.exo.gait_state_estimator.forceplate.ZMQ_PubSub import Subscriber
from src.settings.constants import IP_ADDRESSES

class GaitStateEstimatorThread(BaseWorkerThread):
    """
    Threading class for the Gait State Estimator.
    This class handles gait state estimation for BOTH exoskeletons/sides together.
    """

    def __init__(self,
                 msg_router,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 log_event: Type[threading.Event],
                 active_actuators:list[str],
                 name:Optional[str] = None,
                 frequency:int=100)->None:

        super().__init__(quit_event, pause_event, log_event, name=name, frequency=frequency)

        self.msg_router = msg_router
        self.inbox = None # will be instantiated

        self.active_actuators = active_actuators
        self.bertec_estimators = {}

        self.time_since_start = 0
        self.thread_start_time = time.perf_counter()

        # for each active actuator, initialize GSE Bertec
        for actuator in self.active_actuators:
            selected_topic = f"fz_{actuator}"  # e.g., 'fz_left' or 'fz_right'

            # TODO: REMOVE -- FOR TESTING ONLY
            walker = WalkingSimulator(stride_period=1.20)
            walker.set_percent_toe_off(67)

            self.bertec_estimators[actuator] = walker

            # TODO: UNCOMMENT
            # bertec_subscriber = Subscriber(publisher_ip=IP_ADDRESSES.VICON_IP, topic_filter=selected_topic, timeout_ms=5)
            # self.bertec_estimator[actuator] = Bertec_Estimator(zmq_subscriber=bertec_subscriber)

            # track vars for csv logging
            self.data_logger.track_variable(lambda: self.time_since_start, f"{actuator}_time_since_start")
            self.data_logger.track_variable(lambda: self.bertec_estimators[actuator].stride_start_time, f"{actuator}_HS_time_")
            self.data_logger.track_variable(lambda: self.bertec_estimators[actuator].stride_period, f"{actuator}_stride_period")
            self.data_logger.track_variable(lambda: self.bertec_estimators[actuator].in_swing_flag, f"{actuator}_in_swing_flag_bool")
            self.data_logger.track_variable(lambda: self.bertec_estimators[actuator].current_time_in_stride, f"{actuator}_current_time_in_stride")
            self.data_logger.track_variable(lambda: self.bertec_estimators[actuator].current_percent_gait_cycle, f"{actuator}_current_percent_gait_cycle")

    def pre_iterate(self)->None:
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

            # TODO: update the gait state estimator for the actuator
            # self.bertec_estimators[actuator].update()
            self.bertec_estimators[actuator].update()

            # update csv logger
            self.data_logger.update()

            # send message to actuator inboxes
            try:
                self.data_logger.debug(self.bertec_estimators[actuator].return_estimate())

                msg_router.send(sender=self.name,
                                recipient=actuator,
                                contents=self.bertec_estimators[actuator].return_estimate())
            except:
                self.data_logger.debug(f"UNABLE TO SEND msg to '{actuator}' actuator from GaitStateEstimatorThread. Skipping.")
                continue

    def post_iterate(self)->None:
        pass

    def on_pause(self)->None:
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

    def __init__(self,
                 msg_router,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 log_event: Type[threading.Event],
                 active_actuators:list[str],
                 name:Optional[str] = None,
                 frequency:int=100)->None:


        super().__init__(quit_event, pause_event, log_event, name=name, frequency=frequency)

        self.msg_router = msg_router
        self.inbox = None
        self.active_actuators = active_actuators
        self.torque_setpoint:float = 20.0

        self.thread_start_time:float = time.perf_counter()
        self.time_since_start:float = 0.0

        # track vars for csv logging
        self.data_logger.track_variable(lambda: self.torque_setpoint, "torque_setpt")

        # TODO: connect to existing GUI communication module:
        self.exoboot_remote_servicer = ExobootCommServicer(self.mainwrapper, startstamp, filingcabinet, usebackup=usebackup, quit_event=self.quit_event)


    def pre_iterate(self)->None:
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
        self.torque_setpoint = random.randint(1,4)*10

        for actuator in self.active_actuators:
            try:
                msg_router.send(sender=self.name,
                                recipient=actuator,
                                contents={"torque_setpoint": self.torque_setpoint})
            except:
                self.data_logger.debug(f"UNABLE TO SEND msg to actuator from GUICommunication thread. Skipping.")

    def post_iterate(self)->None:
        pass

    def on_pause(self)->None:
        pass


# Mini Exoboots Robot Class for testing threading
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from dephyEB51 import DephyEB51Actuator
from opensourceleg.logging import LOGGER
from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS
from typing import Union, Dict
import time


class DephyExoboots(RobotBase[DephyEB51Actuator, SensorBase]):

    def start(self) -> None:
        """
        Start the Exoskeleton.
        """
        super().start()

    def stop(self) -> None:
        """
        Stop the Exoskeleton.
        """

        super().stop()

    def set_actuator_mode_and_gains(self, actuator)-> None:
        """
        Call the setup_controller method for all actuators.
        This method selects current control mode and sets PID gains for each actuator.
        """
        actuator.set_control_mode(CONTROL_MODES.CURRENT)
        LOGGER.info("finished setting control mode")

        actuator.set_current_gains(
            kp=DEFAULT_CURRENT_GAINS.kp,
            ki=DEFAULT_CURRENT_GAINS.ki,
            kd=DEFAULT_CURRENT_GAINS.kd,
            ff=DEFAULT_CURRENT_GAINS.ff,
        )
        LOGGER.info("finished setting gains")

    def update(self) -> None:
        """
        Update the exoskeleton.
        """
        # print(f"Updating exoskeleton robot: {self.tag}")
        super().update()

    def spool_belts(self):
        """
        Spool the belts of both actuators.
        This method is called to prepare the actuators for operation.
        """
        for actuator in self.actuators.values():
            actuator.spool_belt()
            LOGGER.info(f"finished spooling belt of {actuator.side}")

    def set_to_transparent_mode(self):
        """
        Set the exo currents to 0mA.
        """
        self.update_current_setpoints(current_inputs=0, asymmetric=False)
        self.command_currents()

    def detect_active_actuators(self) -> Union[str, list[str]]:
        """
        Detect active actuators.
        Returns a string if only one actuator is active, otherwise a list of strings.
        """

        active_sides = list(self.actuators.keys())

        if len(active_sides) == 1:
            return active_sides[0]

        return active_sides

    def create_current_setpts_dict(self) -> None:
        """
        create dictionary of current setpoints (in mA) corresponding to actuator side
        """
        self.current_setpoints = {}
        for actuator in self.actuators.values():
            self.current_setpoints[actuator.side] = 0.0

        # TODO: generate test to determine if current_setpoints dict has the same keys as the actuators dict

    def update_current_setpoints(self, current_inputs: Union[int, Dict[str, int]], asymmetric:bool=False) -> None:
        """
        Directly assign currents to the 'current_setpoints' dictionary for current control.

        If symmetric, the same current value is applied to both sides (with motor sign).
        If asymmetric, the user must pass a dictionary specifying currents for each side.

        Args:
            - current: int or dict. If symmetric=False, this should be a dict with 'left' and 'right' keys.
            - asymmetric: bool. If True, use side-specific currents from the dictionary.
        """
        # TODO: ensure that current_inputs matches the number of active sides
            # TODO: if more than the number of active sides provided, trim to active one only
            # TODO: handle missing sides

        # TODO: clip current setpoints to below max limit

        if asymmetric:
            for side, current in current_inputs.items():    # assign different currents for each actuator
                actuator = getattr(self, side)
                self.current_setpoints[side] = int(current) * actuator.motor_sign
        else:
            for side in self.actuators.keys():              # assign the same current for both actuators
                actuator = getattr(self, side)
                self.current_setpoints[side] = int(current_inputs) * actuator.motor_sign

    def convert_torque_to_current_setpoints(self, torque_setpoint: float) -> dict:
        """
        Find the appropriate current setpoint for the actuators.
        This method is called to determine the current setpoint based on the torque setpoint.

        arguments:
            torque_setpoint: float, the desired torque setpoint in Nm.


        returns:
            current_setpoints:   dict of currents for each active actuator.
                        key is the side of the actuator (left or right).
        """
        for actuator in self.actuators.values():
            self.current_setpoints[actuator.side] = actuator.torque_to_current(torque_setpoint)
            LOGGER.info(f"finished finding current setpoint for {actuator.side}")

            return self.current_setpoints

    def command_currents(self) -> None:
        """
        Commands current setpoints to each actuator based on the current_setpoints dictionary.
        The setpoints can be unique.
        """
        # TODO: ensure current_setpoints values are integers, no greater than max current limit, and are not None

        for actuator in self.actuators.values():

            current_setpoint = self.current_setpoints.get(actuator.side)

            if current_setpoint is not None:
                actuator.set_motor_current(current_setpoint)
                LOGGER.info(f"Finished setting current setpoint for {actuator.side}")
            else:
                LOGGER.warning(f"Unknown side '{actuator.side}' and unable to command current. Skipping.")

    def initialize_rt_plots(self) -> list:
        """
        Initialize real-time plots for the exoskeleton robot.
        Naming and plotting is flexible to each active actuator.

        The following time series are plotted:
        - Current (A)
        - Temperature (°C)
        - Ankle Angle (°)
        - Transmission Ratio
        - Ankle Torque Setpoint (Nm)

        """
        # converting actuator dictionary keys to a list
        active_sides_list = list(self.actuators.keys())

        print("Active actuators:", active_sides_list)

        # pre-slice colors based on the number of active actuators
        colors = ['r', 'b'][:len(active_sides_list)]
        if len(active_sides_list) > len(colors):
            raise ValueError("Not enough unique colors for the number of active actuators.")

        # repeat line styles and widths for each active actuator
        line_styles = ['-' for _ in active_sides_list]
        line_widths = [2 for _ in active_sides_list]

        current_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Exo Current (A) vs. Sample",
                        'ylabel': "Current (A)",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,30]
                        }

        temp_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Case Temperature (°C) vs. Sample",
                        'ylabel': "Temperature (°C)",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [20,60]
                        }

        in_swing_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Bertec in-swing vs. Sample",
                        'ylabel': "Bool",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,150]
                        }

        TR_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "TR (°) vs. Sample",
                        'ylabel': "N",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,20]
                        }

        imu_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Activations vs. Sample",
                        'ylabel': "Bool",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,50]
                        }

        plot_config = [current_plt_config, temp_plt_config, in_swing_plt_config, TR_plt_config, imu_plt_config]

        return plot_config

    def update_rt_plots(self, bertec_swing_flag, imu_activations) -> list:
        """
        Updates the real-time plots with current values for:
        - Current (A)
        - Temperature (°C)
        - Bertec In swing
        - Transmission Ratio
        - IMU estimator activations

        The data is collected from the exoboots object and returned as a list of arrays.
        This is done for each active actuator only.

        Returns:
            plot_data_array: A list of data arrays (for active actuators) for each plot.
        """

        data_to_plt = []

        for actuator in self.actuators.values():
            data_to_plt.extend([
                abs(actuator.motor_current),  # Motor current
                actuator.case_temperature,    # Case temperature
                bertec_swing_flag,
                actuator.gear_ratio,          # Gear ratio
                imu_activations
            ])

        return data_to_plt

    def track_variables_for_logging(self, logger: Logger) -> None:
        """
        Track variables for each active actuator for logging to a single file
        """

        for actuator in self.actuators.values():
            dummy_grpc_value = 5.0
            dummy_ankle_torque_setpt = 20
            logger.track_variable(lambda: time.time(), "pitime")
            logger.track_variable(lambda: dummy_grpc_value, "dollar_value")
            logger.track_variable(lambda: dummy_ankle_torque_setpt, "torque_setpt_Nm")

            logger.track_variable(lambda: actuator.accelx, f"{actuator._tag}_accelx_mps2")
            logger.track_variable(lambda: actuator.motor_current, f"{actuator._tag}_current_mA")
            logger.track_variable(lambda: actuator.motor_position, f"{actuator._tag}_position_rad")
            logger.track_variable(lambda: actuator.motor_encoder_counts, f"{actuator._tag}_encoder_counts")
            logger.track_variable(lambda: actuator.case_temperature, f"{actuator._tag}_case_temp_C")

            tracked_vars = logger.get_tracked_variables()
            print("Tracked variables:", tracked_vars)

    @property
    def left(self) -> DephyEB51Actuator:
        try:
            return self.actuators["left"]
        except KeyError:
            LOGGER.error("Ankle actuator not found. Please check for `left` key in the actuators dictionary.")
            exit(1)

    @property
    def right(self) -> DephyEB51Actuator:
        try:
            return self.actuators["right"]
        except KeyError:
            LOGGER.error("Ankle actuator not found. Please check for `right` key in the actuators dictionary.")
            exit(1)



class ThreadManager:
    """
    This class manages thread creation, communication and termination for the exoskeleton system.
    """

    def __init__(self, msg_router, actuators:Dict) -> None:

        self.actuators = actuators              # Dictionary of Actuators
        self.msg_router = msg_router            # MessageRouter class instance

        # create threading events common to all threads
        self._quit_event = threading.Event()    # Event to signal threads to quit.
        self._pause_event = threading.Event()   # Event to signal threads to pause.
        self._log_event = threading.Event()     # Event to signal threads to log

        # initialize thread events
        self._quit_event.set()      # exo is running
        self._pause_event.clear()   # exo starts paused
        self._log_event.clear()     # exo starts not logging

        # initialize dict of threads
        self._threads = {}

    def start(self) -> None:
        """
        Creates the following threads:
         - for each ACTIVE actuator
         - for the Gait State Estimator
         - for the GUI
        """

        for actuator in self.actuators.values():
            self.initialize_actuator_thread(actuator)

        # creating 1 thread for the Gait State Estimator
        self.initialize_GSE_thread(active_actuators=self.actuators.keys())

        # creating 1 thread for GUI communication
        self.initialize_GUI_thread(active_actuators=self.actuators.keys())

    def start_all_threads(self)->None:
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

    def initialize_actuator_thread(self, actuator:DephyEB51Actuator) -> None:
        """
        Create and start a thread for the specified actuator.
        This method is called to set up the actuator communication thread.
        """

        actuator_thread = ActuatorThread(actuator=actuator,
                                         quit_event=self._quit_event,
                                         pause_event=self._pause_event,
                                         log_event=self._log_event,
                                         name=f"{actuator.side}",
                                         frequency=1000,
                                         msg_router=self.msg_router,
                                         )

        LOGGER.debug(f"created {actuator.side} actuator thread")
        self._threads[actuator.side] = actuator_thread

    def initialize_GSE_thread(self, active_actuators:list[str]) -> None:
        """
        Create and start the Gait State Estimator thread.
        This method is called to set up the GSE communication thread.

        Args:
            active_actuators: List of active actuators to be monitored by the GSE.
                                This is used to initialize the Gait State Estimator.
        """
        # create a FIFO queue with max size for inter-thread communication
        name = "gse"
        gse_thread = GaitStateEstimatorThread(quit_event=self._quit_event,
                                              pause_event=self._pause_event,
                                              log_event=self._log_event,
                                              active_actuators=active_actuators,
                                              name=name,
                                              frequency=250,
                                              msg_router=self.msg_router)

        LOGGER.debug(f"created gse thread")
        self._threads[name] = gse_thread

    def initialize_GUI_thread(self, active_actuators:list[str]) -> None:
        """
        Create and start the GUI thread for user input.
        This method is called to set up the GUI communication thread.
        """

        # create a FIFO queue with max size for inter-thread communication
        name = "gui"
        gui_thread = GUICommunication(quit_event=self._quit_event,
                                      pause_event=self._pause_event,
                                      log_event=self._log_event,
                                      active_actuators=active_actuators,
                                      name=name,
                                      frequency=100,
                                      msg_router=self.msg_router)
        LOGGER.debug(f"created gui thread")
        self._threads[name] = gui_thread

    def return_active_threads(self)->list:
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



# Example main loop
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils.actuator_utils import create_actuators
from src.settings.constants import EXO_SETUP_CONST
from src.utils.walking_simulator import WalkingSimulator
from exoboot_messenger_hub import MessageRouter
from rtplot import client

if __name__ == '__main__':

    # create actuators
    actuators = create_actuators(gear_ratio=1,
                                 baud_rate=EXO_SETUP_CONST.BAUD_RATE,
                                 freq=EXO_SETUP_CONST.FLEXSEA_FREQ,
                                 debug_level=EXO_SETUP_CONST.LOG_LEVEL)

    # create Exoboots Robot
    exoboots = DephyExoboots(tag="exoboots",
                             actuators=actuators,
                             sensors={})

    # create a message router for inter-thread communication
    msg_router = MessageRouter()

    # instantiate thread manager
    system_manager = ThreadManager(msg_router=msg_router, actuators=actuators)

    # instantiate soft real-time clock
    clock = SoftRealtimeLoop(dt = 1 / 1) # Hz

    with system_manager:
        # set-up addressbook for the PostOffice & create inboxes for each thread
        msg_router.setup_addressbook(*system_manager.return_active_threads())

        # start all threads
        system_manager.start_all_threads()

        # unpause exos (removed not from base thread for this to work)
        system_manager._pause_event.set()

        for t in clock:
            try:
                pass

            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break
