import numpy as np
import time
from typing import Union, Dict

from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.robots.base import RobotBase
from opensourceleg.sensors.base import SensorBase
from opensourceleg.utilities import SoftRealtimeLoop

# TODO: fix these next 3 imports:
from src.utils.filing_utils import get_logging_info
from opensourceleg.logging import Logger, LogLevel
CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )
from src.utils import CONSOLE_LOGGER
from opensourceleg.logging import Logger

from src.utils.actuator_utils import create_actuators
from src.settings.constants import (
    EXO_SETUP_CONST,
    DEFAULT_PID_GAINS
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
                kp=DEFAULT_PID_GAINS.KP,
                ki=DEFAULT_PID_GAINS.KI,
                kd=DEFAULT_PID_GAINS.KD,
                ff=DEFAULT_PID_GAINS.FF,
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

    def set_to_transparent_mode(self):
        """
        Set the exo currents to 0mA.
        """
        self.update_current_setpoints(current_inputs=0, asymmetric=False)
        self.command_currents()

    def detect_active_actuators(self) -> Union[start, list[str]]:
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
            currents:   dict of currents for each active actuator.
                        key is the side of the actuator (left or right).
        """
        for actuator in self.actuators.values():
            currents[actuator.side] = actuator.torque_to_current(torque_setpoint)
            CONSOLE_LOGGER.info(f"finished finding current setpoint for {actuator.side}")

            return currents

    def command_currents(self, current_setpoints:dict) -> None:
            self.current_setpoints[actuator.side] = actuator.torque_to_current(torque_setpoint)
            # CONSOLE_LOGGER.info(f"finished finding current setpoint for {actuator.side}")

    def command_currents(self) -> None:
        """
        Commands current setpoints to each actuator.
        The setpoints can be unique.

        arguments:
            current_setpoints: dict of currents for each active actuator.
                              key is the side of the actuator (left or right).
        """

        for actuator in self.actuators.values():
            current_setpoint = current_setpoints.get(actuator.side)

        arguments:
            current_setpoints: dict of currents for each active actuator.
                              key is the side of the actuator (left or right).
        """


        # TODO: ensure current_setpoints values are integers, no greater than max current limit, and are not None

        for actuator in self.actuators.values():
            current_setpoint = current_setpoints.get(actuator.side)

            current_setpoint = self.current_setpoints.get(actuator.side)

            if current_setpoint is not None:
                actuator.set_motor_current(current_setpoint)
                # CONSOLE_LOGGER.info(f"Finished setting current setpoint for {actuator.side}")
            else:
                CONSOLE_LOGGER.warning(f"Unknown side '{actuator.side}' and unable to command current. Skipping.")

    def initialize_rt_plots(self)->list:
                CONSOLE_LOGGER.warning(f"Unknown side '{actuator.side}' and unable to command current. Skipping.")

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

    def update_rt_plots(self, bertec_swing_flag, imu_activations)->list:

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
    actuators = create_actuators(1, EXO_SETUP_CONST.BAUD_RATE, EXO_SETUP_CONST.FLEXSEA_FREQ, EXO_SETUP_CONST.LOG_LEVEL)
    sensors = {}

    # instantiate an exoskeleton robot
    exoboots = DephyExoboots(
        tag="exoboots",
        actuators=actuators,
        sensors=sensors
    )

    # create a soft real-time loop clock
    clock = SoftRealtimeLoop(dt = 1 / EXO_SETUP_CONST.FLEXSEA_FREQ/2)

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