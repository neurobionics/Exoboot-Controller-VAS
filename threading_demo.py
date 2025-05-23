# Abstract Base class for threading
import threading
import logging
from typing import Type
from abc import ABC, abstractmethod
from src.utils.flexible_sleeper import FlexibleSleeper
from opensourceleg.logging import Logger, LogLevel
from non_singleton_logger import NonSingletonLogger

class BaseWorkerThread(threading.Thread, ABC):
    """
    Abstract base class for worker threads in the exoskeleton system.
    
    This class provides a template for creating threads that can be paused and quit.
    It includes methods for thread lifecycle management and a run method that
    handles the thread's main loop.
    """
    def __init__(self, quit_event:Type[threading.Event], pause_event:Type[threading.Event], name=None, frequency:float=100):
        super().__init__(name=name)
        self.quit_event = quit_event
        self.pause_event = pause_event
        self.daemon = True
        self.frequency = frequency
        
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
        
    def run(self):        
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
    def __init__(self, actuator, quit_event:Type[threading.Event], pause_event:Type[threading.Event], name=None, frequency:int=100):
        super().__init__(quit_event, pause_event, name=name or actuator.side, frequency=frequency)
        self.actuator = actuator

    def pre_iterate(self):
        pass
    
    def iterate(self):
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """
        self.actuator.update()
        self.data_logger.debug(f"motor position: {self.actuator.motor_position:.2f}")
        
        # TODO: create a queue that can send the actuator state to the DephyExoboots Robot class

    def post_iterate(self):        
        self.rt_loop.pause()
    
    def on_pause(self):
        pass
    

class GaitStateEstimatorThread(BaseWorkerThread):
    """
    Threading class for the Gait State Estimator.
    This class handles gait state estimation for BOTH exoskeletons/sides together. 
    """
    def __init__(self, quit_event:Type[threading.Event], pause_event:Type[threading.Event], name=None, frequency:int=100):
        super().__init__(quit_event, pause_event, name=name, frequency=frequency)
        
        # instantiate the walking simulator
        self.walker = WalkingSimulator(stride_period=1.20)
    
    def pre_iterate(self):
        pass
    
    def iterate(self):
        """
        Main loop for the actuator thread.
        This method is called repeatedly in the thread's run loop.
        It handles the actuator's state updates.
        """
        self.time_in_stride = self.walker.update_time_in_stride()
        self.ank_angle = self.walker.update_ank_angle()
        
        self.data_logger.debug(f"Stride: {self.walker.stride_num}") 
        self.data_logger.debug(f"Time in stride: {self.time_in_stride:.3f}s")
        self.data_logger.debug(f"Ankle angle: {self.ank_angle:.2f} deg")
        self.data_logger.debug(f"%_GC: {self.walker.percent_gc}")

        # TODO: create a queue that can send the gait state to the DephyExoboots Robot class
    
    def post_iterate(self):        
        self.rt_loop.pause()
    
    def on_pause(self):
        pass


import sys
import select
import zmq
class GUICommunication(BaseWorkerThread):
    """
    Threading class to simulate GUI communication via gRPC.
    This class handles GUI communication for BOTH exoskeletons/sides together. 
    
    It constantly monitors for new user input specifying a desired torque setpoint.
    It then sends these setpoints to the actuators to handle.
    """
    def __init__(self, quit_event:Type[threading.Event], pause_event:Type[threading.Event], name=None, frequency:int=100):
        super().__init__(quit_event, pause_event, name=name, frequency=frequency)
        self.torque_setpoint = 20.0
        
        self.set_up_zmq_socket()  # Set up the ZMQ socket for communication with the GUI
        
    def set_up_zmq_socket(self):
        """
        Set up the ZMQ socket for communication with the GUI.
        This method is called once when the thread is initialized.
        """
        try:
            context = zmq.Context.instance()
            self.pub_socket = context.socket(zmq.PUB)
            self.pub_socket.bind("inproc://torque_setpoint")  # Use inproc for in-process communication
        except Exception as err:
            print(f"Error setting up ZMQ socket: {err}")
            raise err
    
    def publish_torque_setpoint(self, pub_socket, torque_setpoint):
        pub_socket.send_pyobj({"torque_setpoint": torque_setpoint})
    
    def pre_iterate(self):
        pass
    
    def iterate(self):
        """
        Non-blocking: Only read user input if available.
        Allow user to input a new desired torque setpoint. 
        If the user doesn't input a new value, the current setpoint is used.
        """
        pass

        # polling for user input (without blocking thread)
        # if select.select([sys.stdin], [], [], 0.0)[0]:
        #     user_input = sys.stdin.readline().strip()
        #     try:
        #         if user_input == "":
        #             self.data_logger.debug("No new MEANINGFUL input. Using previous torque setpoint.")
        #         else:
        #             self.torque_setpoint = float(user_input)
        #             self.data_logger.debug(f"User input torque setpoint: {self.torque_setpoint:.2f} Nm")
        #     except ValueError:
        #         self.data_logger.debug("Invalid input. Using previous torque setpoint.")
        # else:
        #     self.data_logger.debug("No new input. Using previous torque setpoint.")
            
        # create a queue that can send desired torque setpoint to the main thread
        self.publish_torque_setpoint(self.pub_socket, self.torque_setpoint)
        
    def post_iterate(self):
        self.rt_loop.pause()
    
    def on_pause(self):
        pass
    


# Mini Exoboots Robot Class for testing threading
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from dephyEB51 import DephyEB51Actuator
from opensourceleg.logging import LOGGER
from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS

class DephyExoboots(RobotBase[DephyEB51Actuator, SensorBase]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._threads = {}
        self._quit_event = threading.Event()    # Event to signal threads to quit.
        self._pause_event = threading.Event()   # Event to signal threads to pause.
        
        self._pause_event.set()                 # set to un-paused by default

    def start(self) -> None:
        """Start actuator threads"""
        
        for actuator in self.actuators.values():
            # start the actuator
            actuator.start()
            
            # set-up control modes and gains here before starting the threads
            self.set_actuator_mode_and_gains(actuator)
            
            # creating and starting threads for each actuator
            actuator_thread = ActuatorThread(actuator, self._quit_event, self._pause_event, name=f"{actuator.side}", frequency=1)
            actuator_thread.start()
            LOGGER.debug(f"Started actuator thread for {actuator.side}")
            self._threads[actuator.side] = actuator_thread

        # creating thread for the Gait State Estimator
        gse_thread = GaitStateEstimatorThread(self._quit_event, self._pause_event, name=f"gse", frequency=1)
        gse_thread.start()
        LOGGER.debug(f"Started gse thread")
        self._threads["gse"] = gse_thread

        # creating thread for GUI communication
        gui_thread = GUICommunication(self._quit_event, self._pause_event, name=f"gui", frequency=1)
        gui_thread.start()
        LOGGER.debug(f"Started gui thread")
        self._threads["gui"] = gui_thread

    def stop(self) -> None:
        """Signal threads to quit and join them"""
        # setting the quit event so all threads recieve the kill signal
        self._quit_event.set()
        
        for t in self._threads.values():
            t.join()
        LOGGER.debug("All threads joined to stop.")
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
        
    def update(self):
        """Required by RobotBase, but passing since ActuatorThread handles iterative exo state updates"""
        pass
    
    def find_instantaneous_torque_setpoints(self,):
        """" 
        Determine the instantaneous torque setpoint along the four-point spline assistance profile.
        """
        # TODO: call on assistance generator class to determine the instantaneous torque setpoint
            # TODO: create a dictionary of setpoints for each active (left/right) actuator
        pass

    @property
    def left_thread(self):
        """Get the left actuator thread"""
        return self._actuator_threads.get("left")
    
    @property
    def right_thread(self):
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

def get_torque_setpoint(sub_socket):
    try:
        msg = sub_socket.recv_pyobj(flags=zmq.NOBLOCK)
        return msg["torque_setpoint"]
    except zmq.Again:
        return None

def set_up_zmq_sub_socket():
    """
    Set up the ZMQ socket for communication with the GUI.
    This method is called once when the thread is initialized.
    """
    try:
        context = zmq.Context.instance()
        sub_socket = context.socket(zmq.SUB)
        sub_socket.connect("inproc://torque_setpoint")  # Use inproc for in-process communication
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics
        
        return sub_socket
    except Exception as err:
        print(f"Error setting up ZMQ sub socket: {err}")
        raise err
    
    
if __name__ == '__main__':
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    exoboots = DephyExoboots(tag="exoboots", actuators=actuators, sensors={})
    clock = SoftRealtimeLoop(dt = 1 / 1) # Hz

    with exoboots:  
        sub_socket = set_up_zmq_sub_socket()
        
        for t in clock:
            try:
                # ... insert high level controller logic ...
                pass
                
                # TODO: report current gait state using simulated walking in gse thread

                # TODO: report PEAK torque setpoint using gui thread
                torque = get_torque_setpoint(sub_socket)
                
                if torque is not None:
                    print(f"Received torque setpoint: {torque}")
                else:
                    print("No new torque setpoint received.")

                # TODO: pass reported values into AssistanceGenerator class -> method is part of Exoboots Robot class
                    # TODO: determine appropriate torque setpoint given current gait state

                # TODO: send torque setpoints to each corresponding actuator
                # TODO: determine appropriate current setpoint that matches the torque setpoint -> handled by DephyEB51Actuator class (within each actuator thread)
                # TODO: command appropriate current setpoint using DephyExoboots class

                # TODO: handle logging of actuator state, gait state, torque setpoints, etc. ~ maybe each thread has its own csv logger?
                
            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                exoboots.stop()
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                exoboots.stop()
                break
