# Abstract Base class for threading
import threading
import logging
from typing import Type, Dict, Any, Optional
from abc import ABC, abstractmethod
from src.utils.flexible_sleeper import FlexibleSleeper
from non_singleton_logger import NonSingletonLogger
from dephyEB51 import DephyEB51Actuator

import queue

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
                 name:Optional[str]=None,
                 frequency:int=100)->None:

        super().__init__(name=name)
        self.quit_event = quit_event    # event to signal quitting
        self.pause_event = pause_event  # event to signal pausing

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
            stream_level=logging.INFO
        )

    def run(self)->None:
        """
        Main loop structure for each instantiated thread.
        """
        LOGGER.debug(f"[{self.name}] Thread running.")

        while not self.quit_event.is_set(): # while not quitting
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
                 actuator,
                 data_queue:queue,
                 quit_event: Type[threading.Event],
                 pause_event: Type[threading.Event],
                 name: Optional[str] = None,
                 frequency: int = 100) -> None:

        self.actuator_queue = data_queue  # Queue for inter-thread communication
        super().__init__(quit_event, pause_event, name=name or actuator.side, frequency=frequency)

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
        pass

    def on_pause(self)->None:
        pass


class GaitStateEstimatorThread(BaseWorkerThread):
    """
    Threading class for the Gait State Estimator.
    This class handles gait state estimation for BOTH exoskeletons/sides together.
    """
    def __init__(self,
                 data_queue:queue,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 name:Optional[str] = None,
                 frequency:int=100)->None:

        self.gse_queue = data_queue
        super().__init__(quit_event, pause_event, name=name, frequency=frequency)

        # instantiate the walking simulator
        self.walker = WalkingSimulator(stride_period=1.20)

        # TODO: initialize GSE Bertec here

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
        self.data_logger.debug(f"Stride: {self.walker.stride_num}")
        self.data_logger.debug(f"Time in stride: {self.time_in_stride:.3f}s")
        self.data_logger.debug(f"Ankle angle: {self.ank_angle:.2f} deg")
        self.data_logger.debug(f"%_GC: {self.walker.percent_gc}")

        # Put gait state into the queue for the main thread
        self.enqueue_gait_states()

    def enqueue_gait_states(self)-> None:
        """
        Stores a dict of gait states in the queue for the main thread.
        This method is called to send the gait state to the main thread.
        """
        self.gse_queue.put({
            "time_in_stride": self.time_in_stride,
            "ank_angle": self.ank_angle,
            "percent_gc": self.walker.percent_gc
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
                 data_queue:queue,
                 quit_event:Type[threading.Event],
                 pause_event:Type[threading.Event],
                 name:Optional[str] = None,
                 frequency:int=100)->None:

        self.gui_queue = data_queue
        super().__init__(quit_event, pause_event, name=name, frequency=frequency)

        self.torque_setpoint = 20.0

    def pre_iterate(self)->None:
        pass

    def iterate(self):
        """
        Non-blocking: Only read user input if available.
        Allow user to input a new desired torque setpoint.
        If the user doesn't input a new value, the current setpoint is used.
        """

        # Put the torque setpoint into the queue for the main thread
        self.enqueue_GUI_input()

    def enqueue_GUI_input(self)-> None:
        """
        Stores a dict of GUI inputs in the queue for the main thread.
        This method is called to send the GUI input to the main thread.
        """
        self.gui_queue.put({"torque_setpoint": self.torque_setpoint})

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
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Exoboot Robot class that extends RobotBase.
        This class manages thread creation, data queue creation & management, as well as basic actuator control.
        It is designed to handle multiple actuators and their respective threads, as well as a
        Gait State Estimator (GSE) thread and a GUI communication thread.
        """
        super().__init__(*args, **kwargs)
        self._threads = {}
        self._quit_event = threading.Event()    # Event to signal threads to quit.
        self._pause_event = threading.Event()   # Event to signal threads to pause.

        self._pause_event.set()                 # set to un-paused by default

        # create a dictionary of queues for inter-thread communication
        self.queues: Dict[str, queue.Queue] = {}

    def start(self) -> None:
        """Start actuator threads"""

        for actuator in self.actuators.values():
            # start the actuator
            actuator.start()

            # set-up control modes and gains here before starting the threads
            self.set_actuator_mode_and_gains(actuator)

            # creating and starting a thread for EACH actuator
            self.initialize_actuator_thread(actuator)

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

    def decode_message(self, name: str, key_list: Optional[list[str]] = None) -> Optional[Any]:
        """
        Try to receive a message from named queues. Names are: "gse_queue", "gui_queue", "left_exo_queue", "right_exo_queue".
        If key_list is provided as a list of keys, return a tuple of those values (even if length 1).
        If key_list is a single string, return just that value.
        If key_list is None, return the full message dict.

        Args:
            name (str): The name of the queue to receive from.
            key_list (list[str] or None): List of keys to extract from the message dict. If None, return the full message.
        Returns:
            Any: The received value(s) or None if no message is available.
        """
        # get the queue from the dictionary using the name
        messenger_queue = self.queues.get(name)

        if messenger_queue is None:
            raise ValueError(f"No messenger queue named {name}")

        # if queue name does exist, try to get a message from it
        try:
            msg = messenger_queue.get_nowait()

            # if key_list provided, check whether it is a list or single string
            if key_list is not None:
                if isinstance(key_list, str):
                    return msg.get(key_list)    # return just that requested value
                elif isinstance(key_list, list):
                    return tuple(msg.get(k) for k in key_list)  # return a tuple of requested values
            else:
                return msg  # if no key_list provided, return the full message dict

        except queue.Empty:
            print(f"No new message in {name} queue.")
            return None

    def initialize_actuator_thread(self, actuator: DephyEB51Actuator) -> None:
        """
        Create and start a thread for the specified actuator.
        This method is called to set up the actuator communication thread.
        """
        # create a FIFO queue with max size for inter-thread communication
        actuator_queue = self.create_interthread_queue(actuator.side, max_size=0)

        actuator_thread = ActuatorThread(actuator=actuator,
                                         data_queue=actuator_queue,
                                         quit_event=self._quit_event,
                                         pause_event=self._pause_event,
                                         name=f"{actuator.side}",
                                         frequency=1,
                                         )

        actuator_thread.start()
        LOGGER.debug(f"Started actuator thread for {actuator.side}")
        self._threads[actuator.side] = actuator_thread

    def initialize_GSE_thread(self) -> None:
        """
        Create and start the Gait State Estimator thread.
        This method is called to set up the GSE communication thread.
        """
        # create a FIFO queue with max size for inter-thread communication
        name = "gse"
        gse_queue = self.create_interthread_queue(name, max_size=0)

        gse_thread = GaitStateEstimatorThread(quit_event=self._quit_event,
                                              pause_event=self._pause_event,
                                              name=name,
                                              frequency=1,
                                              data_queue=gse_queue)

        gse_thread.start()
        LOGGER.debug(f"Started gse thread")
        self._threads[name] = gse_thread

    def initialize_GUI_thread(self) -> None:
        """
        Create and start the GUI thread for user input.
        This method is called to set up the GUI communication thread.
        """

        # create a FIFO queue with max size for inter-thread communication
        name = "gui"
        gui_queue = self.create_interthread_queue(name, max_size=0)

        gui_thread = GUICommunication(quit_event=self._quit_event,
                                      pause_event=self._pause_event,
                                      name=name,
                                      frequency=1,
                                      data_queue=gui_queue)
        gui_thread.start()
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

    def find_instantaneous_torque_setpoints(self):
        """"
        Determine the instantaneous torque setpoint along the four-point spline assistance profile.
        """
        # TODO: call on assistance generator class to determine the instantaneous torque setpoint
            # TODO: create a dictionary of setpoints for each active (left/right) actuator
        pass

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
        return self._actuator_threads.get("left")

    @property
    def right_thread(self) -> Optional[ActuatorThread]:
        """Get the right actuator thread"""
        return self._actuator_threads.get("right")


# Example main loop
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils.actuator_utils import create_actuators
from src.settings.constants import(
    BAUD_RATE,
    FLEXSEA_FREQ,
    LOG_LEVEL
)
from src.utils.walking_simulator import WalkingSimulator

if __name__ == '__main__':
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    exoboots = DephyExoboots(tag="exoboots", actuators=actuators, sensors={})
    clock = SoftRealtimeLoop(dt = 1 / 1) # Hz

    with exoboots:

        for t in clock:
            try:

                # report current gait state using simulated walking in gse thread
                gse_msg = exoboots.decode_message("gse", key_list=["time_in_stride", "percent_gc"])
                if gse_msg is not None:
                    time_in_stride, percent_gc = gse_msg # unpackage the message
                    print(f"Received gait state: time_in_stride={time_in_stride}, percent_gc={percent_gc}")
                else:
                    print("No new gait state received.")

                # report PEAK torque setpoint using gui thread
                torque = exoboots.decode_message("gui", key_list="torque_setpoint")
                if torque is not None:
                    print(f"Received torque setpoint: {torque}")
                else:
                    print("No new torque setpoint received.")

                # report actuator state from each actuator thread queue
                for actuator in exoboots.actuators.values():
                    actuator_msg = exoboots.decode_message(actuator.side, key_list=["motor_current", "temperature"])
                    if actuator_msg is not None:
                        current_setpoint, temperature = actuator_msg
                        print(f"Received {actuator.side} actuator state: current_setpoint={current_setpoint}, temperature={temperature}")
                    else:
                        print(f"No new {actuator.side} actuator state received.")


                # TODO: pass reported values into AssistanceGenerator class -> method is part of Exoboots Robot class
                    # TODO: determine appropriate torque setpoint given current gait state

                # TODO: send torque setpoints to each corresponding actuator
                # TODO: determine appropriate current setpoint that matches the torque setpoint -> handled by DephyEB51Actuator class (within each actuator thread)
                # TODO: command appropriate current setpoint using DephyExoboots class

                # TODO: handle logging of actuator state, gait state, torque setpoints, etc. ~ maybe each thread has its own csv logger?

            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break
