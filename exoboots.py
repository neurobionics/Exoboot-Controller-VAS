import numpy as np
import time

from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DEFAULT_CURRENT_GAINS
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils import CONSOLE_LOGGER
from opensourceleg.logging import Logger, LogLevel

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

    def initialize_JIM_rt_plots(self)->list:
        """
        Initialize plots for JIM data streaming
        The following time series are plotted:
            - Current (A)
            - Temperature (°C)
            - Ankle Angle (°)
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

        ang_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Ank Angle vs. Sample",
                        'ylabel': "°",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,150]
                        }

        plot_config = [current_plt_config, temp_plt_config, ang_plt_config]

        return plot_config

    def update_JIM_rt_plots(self, bertec_swing_flag, imu_activations)->list:
        """
        Updates the real-time plots with current values while JIM testing:
            - Current (A)
            - Temperature (°C)
            - Ankle Angle

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
                actuator.ankle_angle          # Ankle Angle
            ])

        return data_to_plt

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

    def update_rt_plots(self, bertec_swing_flag, imu_activations)->list:
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
            logger.track_variable(lambda: time.time(), f"pitime")
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