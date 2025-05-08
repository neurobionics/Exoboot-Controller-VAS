from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS, DephyLegacyActuator
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from opensourceleg.utilities import SoftRealtimeLoop

from src.utils.actuator_utils import create_actuators
from src.settings.constants import (
    BAUD_RATE,
    LOG_LEVEL,
    FLEXSEA_FREQ,
)


class DephyExoboots(RobotBase[DephyLegacyActuator, SensorBase]):
    """
    Bilateral Dephy EB51 Exoskeleton class derived from RobotBase.
    
    This class creates a DephyExoboots Robot, using the structure
    provided by the RobotBase class. A robot is composed of a collection 
    of actuators and sensors. 
    
    """
    
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

    def update(self) -> None:
        """
        Update the exoskeleton.
        """
        print(f"Updating exoskeleton robot: {self.tag}")
        super().update()
      
    def setup_control_modes(self) -> None:
        """
        Call the setup_controller method for all actuators.
        This method selects current control mode and sets PID gains for each actuator.
        """
        
        for actuator in self.actuators.values():
            actuator.set_control_mode(CONTROL_MODES.CURRENT)
            print("finished setting control mode")
            
            actuator.set_current_gains(
                kp=DEFAULT_CURRENT_GAINS.kp,
                ki=DEFAULT_CURRENT_GAINS.ki,
                kd=DEFAULT_CURRENT_GAINS.kd,
                ff=DEFAULT_CURRENT_GAINS.ff,
            )
            print("finished setting gains")
        
    @property
    def left(self) -> DephyLegacyActuator:
        return self.actuators["left"]

    @property
    def right(self) -> DephyLegacyActuator:
        return self.actuators["right"]
  
    
# DEMO:
if __name__ == "__main__":
    
    # define dictionary of actuators & sensors
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    sensors = {}

    # instantiate an exoskeleton robot
    exoboots = DephyExoboots(
        tag="exoboots", 
        actuators=actuators, 
        sensors=sensors
    )

    # create a soft real-time loop clock
    clock = SoftRealtimeLoop(dt = 1 / FLEXSEA_FREQ/2) 

    # use exoskeleton robot class as the context manager
    with exoboots:
        
        # setup the exo controller
        exoboots.setup_control_modes()
            
        # run the main control loop
        for t in clock:
            try:
                print(f"Time: {t:.2f} seconds")
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break