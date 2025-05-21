# Abstract Base class for threading
import threading
from typing import Type
import time
from abc import ABC, abstractmethod
from src.utils.flexible_sleeper import FlexibleSleeper

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
        
        self.rt_loop = FlexibleSleeper(dt=1/frequency)  # Create a soft real-time loop with the specified frequency             #
        
    def run(self):
        LOGGER.debug(f"[{self.name}] Thread running.")
        while not self.quit_event.is_set():     # while the quit event isn't set (meaning it is running)
            if not self.pause_event.is_set():   # if the pause event isn't set (meaning it is paused)
                continue
            try:
                self.iterate()                  # If not paused, call the iterate method to perform the thread's task
            except Exception as e:
                LOGGER.debug(f"Exception in thread {self.name}: {e}")
            
            self.rt_loop.pause()
            
        LOGGER.debug(f"[{self.name}] Thread exiting.")
        
    @abstractmethod
    def pre_iterate(self):
        """
        Override this abstract method in subclasses to do the thread's work.
        This method contains the main logic for the thread's operation.
        """
        LOGGER.debug(f"[{self.name}] iterate() called.")
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
        Override this abstract method in subclasses to do the thread's work.
        This method contains the main logic for the thread's operation.
        """
        LOGGER.debug(f"[{self.name}] iterate() called.")
        pass

    @abstractmethod 
    def on_pre_pause(self):
        LOGGER.debug(f"[{self.name}] on_pre_pause() called.")
        pass
    
# TODO:
class GSE():
    pass

# TODO: 
class GUICommunication():
    pass

    
# Actuator Thread Class
class ActuatorThread(BaseWorkerThread):
    def __init__(self, actuator, quit_event:Type[threading.Event], pause_event:Type[threading.Event], name=None, frequency:float=100):
        super().__init__(quit_event, pause_event, name=name or actuator.side, frequency=frequency)
        self.actuator = actuator

    def pre_iterate(self):
        pass
    
    def iterate(self):
        self.actuator.update()
        LOGGER.debug(f"[{self.name}] motor position: {self.actuator.motor_position}")
        LOGGER.debug(f"[{self.name}] motor temp: {self.actuator.case_temperature}")
    
    def post_iterate(self):
        pass

    def on_pre_pause(self):
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
        self._actuator_threads = {}
        self._quit_event = threading.Event()    # Event to signal threads to quit.
        self._pause_event = threading.Event()   # Event to signal threads to pause.
        
        self._pause_event.set()                 # set to un-paused by default

    def start(self) -> None:
        """Start actuator threads"""
        
        for actuator in self.actuators.values():
            LOGGER.debug(f"Calling start method of {actuator.tag}")
            actuator.start()
            
            # setting-up control modes and gains here before starting the threads
            self.set_actuator_mode_and_gains(actuator)
            
            # creating and starting threads for each actuator
            thread = ActuatorThread(actuator, self._quit_event, self._pause_event, name=f"{actuator.side}", frequency=1)
            thread.start()
            LOGGER.debug(f"Started thread for {actuator.side}")
            self._actuator_threads[actuator.side] = thread

    def stop(self) -> None:
        """Signal threads to quit and join them"""
        LOGGER.debug("Signaling threads to stop...")
        self._quit_event.set()
        for t in self._actuator_threads.values():
            t.join()
        LOGGER.debug("All threads joined.")
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

if __name__ == '__main__':
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    exoboots = DephyExoboots(tag="exoboots", actuators=actuators, sensors={})
    clock = SoftRealtimeLoop(dt = 1 / 1) # Hz

    with exoboots:
        for t in clock:
            try:
                # ... insert high level controller logic ...
                print(f"Main loop iteration {t:0.2f}")
                
            except KeyboardInterrupt:
                print("KeyboardInterrupt received.")
                exoboots.stop()
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                exoboots.stop()
                break
                