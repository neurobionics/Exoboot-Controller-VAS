from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils import CONSOLE_LOGGER
from src.utils.actuator_utils import create_actuators
from src.settings.constants import (
    BAUD_RATE,
    LOG_LEVEL,
    FLEXSEA_FREQ,
)
from dephyEB51 import DephyEB51Actuator


class DephyExoboots(RobotBase[DephyEB51Actuator, SensorBase]):
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
        # print(f"Updating exoskeleton robot: {self.tag}")
        super().update()
        
    def setup_control_modes(self) -> None:
        """
        Call the setup_controller method for all actuators.
        This method selects current control mode and sets PID gains for each actuator.
        """
        
        for actuator in self.actuators.values():
            actuator.set_control_mode(CONTROL_MODES.CURRENT)
            CONSOLE_LOGGER.info("finished setting control mode")
            
            actuator.set_current_gains(
                kp=DEFAULT_CURRENT_GAINS.kp,
                ki=DEFAULT_CURRENT_GAINS.ki,
                kd=DEFAULT_CURRENT_GAINS.kd,
                ff=DEFAULT_CURRENT_GAINS.ff,
            )
            CONSOLE_LOGGER.info("finished setting gains")
            
    def spool_belts(self):
        """
        Spool the belts of both actuators.
        This method is called to prepare the actuators for operation.
        """
        for actuator in self.actuators.values():
            actuator.spool_belt()
            CONSOLE_LOGGER.info(f"finished spooling belt of {actuator.side}")
            
    def find_current_setpoints(self, torque_setpoint: float) -> dict:
        """
        Find the appropriate current setpoint for the actuators.
        This method is called to determine the current setpoint based on the torque setpoint.
        
        arguments:
            torque_setpoint: float, the desired torque setpoint in Nm.
        
        returns:
            currents:   dict of currents for each active actuator. 
                        key is the side of the actuator (left or right).
        """
        currents = {}
        for actuator in self.actuators.values():
            currents[actuator.side] = actuator.torque_to_current(torque_setpoint)
            CONSOLE_LOGGER.info(f"finished finding current setpoint for {actuator.side}")
            
            return currents
        
    def command_currents(self, current_setpoints:dict) -> None:
        """
        Commands current setpoints to each actuator.
        The setpoints can be unique.
        
        arguments:
            current_setpoints: dict of currents for each active actuator. 
                              key is the side of the actuator (left or right).
        """
        
        for actuator in self.actuators.values():
            current_setpoint = current_setpoints.get(actuator.side)
            
            if current_setpoint is not None:
                actuator.set_motor_current(current_setpoint)
                CONSOLE_LOGGER.info(f"Finished setting current setpoint for {actuator.side}")
            else:
                CONSOLE_LOGGER.warning(f"Unknown side '{actuator.side}' and unable to command current. Skipping.")       
    
    @property
    def left(self) -> DephyEB51Actuator:
        try:
            return self.actuators["left"]
        except KeyError:
            CONSOLE_LOGGER.error("Ankle actuator not found. Please check for `left` key in the actuators dictionary.")
            exit(1)

    @property
    def right(self) -> DephyEB51Actuator:
        try:
            return self.actuators["right"]
        except KeyError:
            CONSOLE_LOGGER.error("Ankle actuator not found. Please check for `right` key in the actuators dictionary.")
            exit(1)
  
    
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