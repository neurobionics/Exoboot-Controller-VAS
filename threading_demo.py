# Abstract Base class for threading
import threading
import logging
from typing import Type, Dict, Any, Optional
from abc import ABC, abstractmethod
from src.utils.flexible_sleeper import FlexibleSleeper
from non_singleton_logger import NonSingletonLogger
from dephyEB51 import DephyEB51Actuator

import queue

from src.utils.filing_utils import get_logging_info
from opensourceleg.logging import Logger, LogLevel
CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )

from Exoboot_Postal_Service import PostOffice

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
        # logger_name = f"{name}_logger"
        # log_path = "./src/logs/"
        # self.data_logger = NonSingletonLogger(
        #     log_path=log_path,
        #     file_name=logger_name,
        #     file_level=logging.DEBUG,
        #     stream_level=logging.INFO
        # )

    def run(self)->None:
        """
        Main loop structure for each instantiated thread.
        """
        LOGGER.debug(f"[{self.name}] Thread running.")

        while self.quit_event.is_set(): # while not quitting
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


class ActuatorThread(BaseWorkerThread):
    """
    Threading class for EACH actuator.
    This class handles the actuator's state updates and manages the actuator's control loop.
    """
    def __init__(self,
                 name: str,
                 actuator,
                 post_office,
                 quit_event: Type[threading.Event],
                 pause_event: Type[threading.Event],
                 log_event: Type[threading.Event],
                 frequency: int = 100) -> None:

        super().__init__(quit_event, pause_event, log_event, name, frequency=frequency)

        self.post_office = post_office
        self.mailbox = None

        self.actuator = actuator

    def pre_iterate(self)->None:
        pass

    def iterate(self)->None:
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """
        self.actuator.update()
        self.data_logger.debug(f"motor position: {self.actuator.motor_position:.2f}")

        # create a queue that can send the actuator state to the DephyExoboots Robot class
        self.enqueue_actuator_states()

    def enqueue_actuator_states(self)-> None:
        """
        Stores a dict of actuators state in the queue for the main thread.
        This method is called to send the actuator's state to the main thread.
        """
        self.actuator_queue.put({
            "motor_current": self.actuator.motor_current,
            "temperature": self.actuator.case_temperature,
        })

    def post_iterate(self)->None:
        # TODO add rest of stuff
        if self.log_event.is_set():
            LOGGER.debug(f"[{self.name}] log_event True")

    def on_pause(self)->None:
        pass


class GaitStateEstimatorThread(BaseWorkerThread):
    """
    Threading class for the Gait State Estimator.
    This class handles gait state estimation for BOTH exoskeletons/sides together.
    """
    def __init__(self,
                 post_office,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 log_event: Type[threading.Event],
                 name:Optional[str] = None,
                 frequency:int=100)->None:

        super().__init__(quit_event, pause_event, log_event, name=name, frequency=frequency)

        self.post_office = post_office
        self.mailbox = None

        # instantiate the walking simulator
        self.walker = WalkingSimulator(stride_period=1.20)


        # TODO: initialize GSE Bertec here

    def pre_iterate(self)->None:
        pass

    def pre_iterate(self)->None:
        pass

    def iterate(self):
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """

        self.time_in_stride = self.walker.update_time_in_stride()
        self.ank_angle = self.walker.update_ank_angle()

        # TODO: do update_bertec_estimator.update() here

        # TODO: DON"T LOG HERE (make ligtweight)
        self.data_logger.debug(f"Time in stride: {self.time_in_stride:.3f}s")
        self.data_logger.debug(f"Ankle angle: {self.ank_angle:.2f} deg")

        # create a queue that can send the gait state to the DephyExoboots Robot class
        self.enqueue_gait_states()

    def post_iterate(self)->None:
        pass

    def enqueue_gait_states(self)-> None:
        """
        Stores a dict of gait states in the queue for the main thread.
        This method is called to send the gait state to the main thread.
        """
        self.gse_queue.put({
            "time_in_stride": self.walker.time_in_stride,
            "ank_angle": self.walker.ank_angle,
        })

    def post_iterate(self)->None:
        pass

    def on_pause(self)->None:
        pass


import sys
import select
class GUICommunication(BaseWorkerThread):
    """
    Threading class to simulate GUI communication via gRPC.
    This class handles GUI communication for BOTH exoskeletons/sides together.

    It constantly monitors for new user input specifying a desired torque setpoint.
    It then sends these setpoints to the actuators to handle.
    """
    def __init__(self,
                 post_office,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 log_event: Type[threading.Event],
                 name:Optional[str] = None,
                 frequency:int=100)->None:


        super().__init__(quit_event, pause_event, log_event, name=name, frequency=frequency)

        self.post_office = post_office
        self.mailbox = None
        self.torque_setpoint = 20.0

    def pre_iterate(self)->None:
        # read mail regardless of paused state
        mail_list = self.mailbox.getmail_all()  # return list of mail
        CONSOLE_LOGGER.debug(f"mail received in GUICommunication thread {len(mail_list)}")

        # unpackage the mail
        for mail in mail_list:
            self.decode_message(mail)
            print(f"torque setpoint is:{self.torque_setpoint}")

    def decode_message(self, mail:list) -> Optional[Any]:
        """
        Decode a message from the mailbox.
        """
        try:
            # example contents {"peak_torque": 30.1, "stride_period": 1.3}
            for key, value in mail["contents"].items():
                #TODO value validation (not None or something)
                setattr(self, key, value)

        except Exception as err:
            LOGGER.debug("Error decoding message:", err)
            return None

    def iterate(self):
        """
        Non-blocking: Only read user input if available.
        Allow user to input a new desired torque setpoint.
        If the user doesn't input a new value, the current setpoint is used.
        """

        # Put the torque setpoint into the queue for the main thread
        pass

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

class DephyExoboots(RobotBase[DephyEB51Actuator, SensorBase]):
    def __init__(self, tag, actuators, sensors, post_office) -> None:
        """
        Exoboot Robot class that extends RobotBase.
        This class manages thread creation, data queue creation & management, as well as basic actuator control.
        It is designed to handle multiple actuators and their respective threads, as well as a
        Gait State Estimator (GSE) thread and a GUI communication thread.
        """
        super().__init__(tag=tag, actuators=actuators, sensors=sensors)
        self._threads = {}
        self._quit_event = threading.Event()    # Event to signal threads to quit.
        self._pause_event = threading.Event()   # Event to signal threads to pause.
        self._log_event = threading.Event()     # Event to signal threads to log
        self.post_office = post_office          # PostOffice class instance

        # Thread event inits
        self._quit_event.set()      # exo is running
        self._pause_event.clear()   # exo starts paused
        self._log_event.clear()     # exo starts not logging

    def start(self) -> None:
        """Start actuator threads"""

        for actuator in self.actuators.values():
            # start the actuator
            actuator.start()

            # set-up control modes and gains here before starting the threads
            self.set_actuator_mode_and_gains(actuator)

            # creating and starting threads for each actuator
            self.initialize_actuator_thread(actuator)
            CONSOLE_LOGGER.debug(f"Started actuator thread for {actuator.side}")

        # creating 1 thread for the Gait State Estimator
        self.initialize_GSE_thread()

        # creating 1 thread for GUI communication
        self.initialize_GUI_thread()

    def stop(self) -> None:
        """Signal threads to quit and join them"""
        # setting the quit event so all threads recieve the kill signal
        self._quit_event.set()
        super().stop()

    def create_interthread_queue(self, name:str, max_size:int=0) -> queue.Queue:
        """
        Create a FIFO queue for inter-thread communication.
        Queues stored in dictionary with the name as the key.

        Args:
            name (str): A unique name for the queue, typically the side of the actuator or thread.
        Returns:
            queue.Queue: A FIFO queue for inter-thread communication.
        """

        # create a FIFO queue with max size for inter-thread communication & store to dictionary
        self.queues[name] = queue.Queue(maxsize=max_size)

        return self.queues[name]

    def initialize_actuator_thread(self, actuator: DephyEB51Actuator) -> None:
        """
        Create and start a thread for the specified actuator.
        This method is called to set up the actuator communication thread.
        """

        actuator_thread = ActuatorThread(actuator=actuator,
                                         quit_event=self._quit_event,
                                         pause_event=self._pause_event,
                                         log_event=self._log_event,
                                         name=f"{actuator.side}",
                                         frequency=1,
                                         post_office=self.post_office,
                                         )

        LOGGER.debug(f"Started actuator thread for {actuator.side}")
        self._threads[actuator.side] = actuator_thread

    def initialize_GSE_thread(self) -> None:
        """
        Create and start the Gait State Estimator thread.
        This method is called to set up the GSE communication thread.
        """
        # create a FIFO queue with max size for inter-thread communication
        name = "gse"
        gse_thread = GaitStateEstimatorThread(quit_event=self._quit_event,
                                              pause_event=self._pause_event,
                                              log_event=self._log_event,
                                              name=name,
                                              frequency=1,
                                              post_office=self.post_office)

        LOGGER.debug(f"Started gse thread")
        self._threads[name] = gse_thread

    def initialize_GUI_thread(self) -> None:
        """
        Create and start the GUI thread for user input.
        This method is called to set up the GUI communication thread.
        """

        # create a FIFO queue with max size for inter-thread communication
        name = "gui"
        gui_thread = GUICommunication(quit_event=self._quit_event,
                                      pause_event=self._pause_event,
                                      log_event=self._log_event,
                                      name=name,
                                      frequency=1,
                                      post_office=self.post_office,)
        LOGGER.debug(f"Started gui thread")
        self._threads[name] = gui_thread

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

    def update(self)->None:
        """Required by RobotBase, but passing since ActuatorThread handles iterative exo state updates"""
        pass

    def return_active_threads(self)->list:
        """
        Return list of active thread addresses.
        """
        return self._threads.values()

    @property
    def left_exo_queue(self) -> Dict[str, queue.Queue]:
        """Get the queue for the left actuator"""
        return self.queues.get("left")

    @property
    def right_exo_queue(self) -> Dict[str, queue.Queue]:
        """Get the queue for the right actuator"""
        return self.queues.get("right")

    @property
    def gse_queue(self) -> Dict[str, queue.Queue]:
        """Get the queue for the gait state estimator"""
        return self.queues.get("gse")

    @property
    def gui_queue(self) -> Dict[str, queue.Queue]:
        """Get the queue for the GUI communication"""
        return self.queues.get("gui")

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

if __name__ == '__main__':

    post_office = PostOffice()

    actuators = create_actuators(1, EXO_SETUP_CONST.BAUD_RATE, EXO_SETUP_CONST.FLEXSEA_FREQ, EXO_SETUP_CONST.LOG_LEVEL)
    exoboots = DephyExoboots(tag="exoboots",
                             actuators=actuators,
                             sensors={},
                             post_office=post_office)
    clock = SoftRealtimeLoop(dt = 1 / 1) # Hz

    with exoboots:
        # set-up addressbook for the PostOffice
        post_office.setup_addressbook(*exoboots.return_active_threads())

        # TODO add start_threads method to DephyExoboots class
        # exoboots.left_thread.start()
        exoboots.right_thread.start()
        exoboots.gse_thread.start()
        exoboots.gui_thread.start()
        CONSOLE_LOGGER.debug("All threads started.")

        for t in clock:
            try:

                # send mail to the GUI thread
                post_office.send(sender="main", recipient="gui", contents={"torque_setpoint": 30.0})
                print("Main sent")

                # TODO: pass reported values into AssistanceGenerator class -> method is part of Exoboots Robot class
                    # TODO: determine appropriate torque setpoint given current gait state

                # TODO: send torque setpoints to each corresponding actuator
                # TODO: determine appropriate current setpoint that matches the torque setpoint -> handled by DephyEB51Actuator class (within each actuator thread)
                # TODO: command appropriate current setpoint using DephyExoboots class

            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break
