import numpy as np

from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS, DephyLegacyActuator
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging import Logger, LogLevel

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
        # print(f"Updating exoskeleton robot: {self.tag}")
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
        
    def initialize_rt_plots(self)->list:
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
        
        ank_ang_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Ankle Angle (°) vs. Sample",
                        'ylabel': "Angle (°)",
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
        
        torque_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Torque (Nm) vs. Sample",
                        'ylabel': "Torque (Nm)",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,50]
                        }

        plot_config = [current_plt_config, temp_plt_config, ank_ang_plt_config, TR_plt_config, torque_plt_config]
        
        return plot_config
        
    def update_rt_plots(self)->list:
        """
        Updates the real-time plots with current values for:
        - Current (A)
        - Temperature (°C)
        - Ankle Angle (°)
        - Transmission Ratio
        - Ankle Torque Setpoint (Nm)
       
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
                80,
                actuator.gear_ratio,          # Gear ratio
                20                            # Torque command
            ])
        
        return data_to_plt
            
    def track_variables_for_logging(self, logger: Logger) -> None:
        """
        Track variables for each active actuator for logging to a single file
        """

        for actuator in self.actuators.values():
            dummy_grpc_value = 5.0
            dummy_ankle_torque_setpt = 20
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