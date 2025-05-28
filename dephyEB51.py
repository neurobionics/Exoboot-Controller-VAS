import time
import numpy as np

from opensourceleg.actuators.dephy import DephyLegacyActuator
from opensourceleg.actuators.base import MOTOR_CONSTANTS
from src.utils import CONSOLE_LOGGER
from opensourceleg.logging import LOGGER

from src.settings.constants import (
    MAX_CASE_TEMP,
    MAX_WINDING_TEMP,
    DEV_ID_TO_MOTOR_SIGN_DICT,
    DEV_ID_TO_ANK_ENC_SIGN_DICT,
    DEV_ID_TO_SIDE_DICT,
    BIAS_CURRENT,
    MAX_ALLOWABLE_CURRENT,
    EB51_CONSTANTS,
    TEMPANTISPIKE
)
from src.exo.variable_transmission_ratio import VariableTransmissionRatio


class DephyEB51Actuator(DephyLegacyActuator):
    """
    DephyEB51 actuator class for controlling the EB51 actuator.
    Inherits from the DephyLegacyActuator class.

    Methods:
        __init__: Initializes the DephyEB51 actuator with custom motor constants.
        set_gear_ratio: Sets the gear ratio for the actuator.
        set_spool_radius: Sets the spool radius for the actuator.
        set_torque_to_current_converter: Sets the torque to current converter for the actuator.
        set_spline_assistance_generator: Sets the spline assistance generator for the actuator.
        home_exos: Homes the exoskeleton at a standing angle.
    Attributes:
        tag: The tag for the actuator.
        port: The port for the actuator.
        baud_rate: The baud rate for the actuator.
        frequency: The frequency for the actuator.
        debug_level: The debug level for the actuator.
        dephy_log: Whether to log Dephy data or not.
        offline: Whether to run in offline mode or not.
        gear_ratio: The gear ratio for the actuator.
        motor_constants: The motor constants for the actuator.
    """

    def __init__(
        self,
        tag: str = "EB51Actuator",
        port: str = "/dev/ttyACM0",
        baud_rate: int = 230400,
        frequency: int = 500,
        debug_level: int = 4,
        dephy_log: bool = False,
        offline: bool = False,
        gear_ratio: float = 1.0,
    ) -> None:

        CONSOLE_LOGGER.info("Initializing DephyEB51 actuator...")

        super().__init__(
            tag,
            port,
            gear_ratio,
            baud_rate,
            frequency,
            debug_level,
            dephy_log,
            offline,
        )

        eb51_motor_constants = MOTOR_CONSTANTS(
            MOTOR_COUNT_PER_REV=2**14,
            NM_PER_AMP=0.146,                           # EB51 specific torque constant
            NM_PER_RAD_TO_K=((2 * np.pi / 16384) / 0.0007812 * 1e3 / 0.146),
            NM_S_PER_RAD_TO_B=((np.pi / 180) / 0.00028444 * 1e3 / 0.146),
            MAX_CASE_TEMPERATURE=MAX_CASE_TEMP,         # Custom max case temperature
            MAX_WINDING_TEMPERATURE=MAX_WINDING_TEMP,   # Custom max winding temperature
        )

        # overwrite the motor constants to the custom EB51 motor constants
        self._MOTOR_CONSTANTS = eb51_motor_constants

        # determine exo side based on device id
        self.side = self.assign_id_to_side()

        # assign motor and ankle encoder signs specific to our EB51 Exoskeletons (CRITICAL - DO NOT CHANGE)
        self.motor_sign = DEV_ID_TO_MOTOR_SIGN_DICT[self.dev_id]
        self.ank_enc_sign = DEV_ID_TO_ANK_ENC_SIGN_DICT[self.dev_id]

        # set current bounds
        self.min_current = BIAS_CURRENT
        self.max_current = MAX_ALLOWABLE_CURRENT

        # create a buffer for the case temperature
        self.case_temp_buffer = []

        # instantiate transmission ratio getter which uses motor-angle curve coefficients from pre-performed calibration
        self.tr_gen = VariableTransmissionRatio(self.side)
        CONSOLE_LOGGER.info("instantiated variable transmission ratio")


    def update_gear_ratio(self)-> None:
        """
        Updates the variable gear ratio of the actuator.
        """
        self._gear_ratio = self.tr_gen.get_TR(self.ankle_angle)

        return self._gear_ratio

    # TODO: recharacterize transmission ratio without ENC_CLICKS_TO_DEG constant. That constant is redundant since Dephy already reports in degrees
    @property
    def ankle_angle(self) -> float:
        """
        Returns the current ankle angle after applying a exoboot specific transformation.
        i.e. minimum ankle angles (approx 0°) corresponds to max dorsiflexion, while max ankle angle corresponds to max plantarflexion.

        Ankle angle is in ° and is the angle of the ankle joint using the ankle encoder. Angles should range anywhere from 0° to 140°.
        """

        if self._data is not None:
            ank_ang_in_deg = self.ank_ang/100
            return float( (self.ank_enc_sign * ank_ang_in_deg) - self.tr_gen.get_offset() )
        else:
            LOGGER.debug(
                msg="Actuator data is none, please ensure that the actuator is connected and streaming. Returning 0.0."
            )
            return 0.0


    def update(self)->None:
        """
        Updates the actuator state.
        """

        # filter the temperature before updating the thermal model
        self.filter_temp()

        super().update()

        # update the gear ratio
        self.update_gear_ratio()


    def assign_id_to_side(self)-> str:
        """
        Determines side (left/right) of the actuator based on previously mapped device ID number.
        """
        side = DEV_ID_TO_SIDE_DICT[self.dev_id]

        return side


    def spool_belt(self)->None:

        LOGGER.info(
            f"Spooling {self.side} joint. "
            "Please make sure the joint is free to move and press Enter to continue."
        )

        input()
        self.set_motor_current(value=self.motor_sign * BIAS_CURRENT)  # in mA

        time.sleep(0.3)


    def filter_temp(self)->None:
        """
        Filters the case temperature to remove any spikes.
        If the temperature is unreasonably high, then it is set to a previous recorded value.
        """

        self.case_temp_buffer.append(self.case_temperature)

        if len(self.case_temp_buffer) > 2:
            self.case_temp_buffer.pop(0)  # remove the oldest element of the list

        if len(self.case_temp_buffer) > 1:
            criteria_one = ( abs(self.case_temperature) > TEMPANTISPIKE )
            criteria_two = (self.case_temperature <= 0)
            criteria_three = ( abs(self.case_temp_buffer[1] - self.case_temp_buffer[0]) ) > 5

            if criteria_one or criteria_two or criteria_three:
                self.case_temperature = self.case_temp_buffer[0]   # set it to the previously recorded temperature

                CONSOLE_LOGGER.warning(f"HAD TO ANTI-SPIKE the TEMP: {self.case_temperature}")


    def torque_to_current(self, torque: float) -> int:
        """
        Converts torque setpoint (Nm) to a corresponding current (in mA)
        given the instantaneous TR (N) and motor constants.

        The output current can only be an integer value.

        Arguments:
            torque: float, the desired torque setpoint in Nm.

        Returns:
            des_current: int, the desired current setpoint in mA.

        """
        des_current = torque / (self.gear_ratio * EB51_CONSTANTS.EFFICIENCY * self._MOTOR_CONSTANTS.NM_PER_AMP)

        # convert to mA and account for motor sign
        des_current = des_current * 1000 * self.motor_sign

        return int(des_current)

    def current_to_torque(self)-> float:
        """
        Converts current setpoint (in mA) to a corresponding torque (in Nm)
        """
        mA_to_A_current = self.motor_current/1000
        des_torque = mA_to_A_current * self._MOTOR_CONSTANTS.NM_PER_AMP * EB51_CONSTANTS.EFFICIENCY * self.motor_sign

        return des_torque

    # TODO: Add method to convert JIM torque-ankle angle look-up table to a specfic current
    def JIM_torque_to_current(self, inst_torque: float) -> int:
        """
        Converts desired, instantaneous torque setpoint to it's corresponding current (in mA)
        depending on the current ankle angle.

        Mapping is derived from the Joint Impedance Machine's torque-angle-current look-up table.

        Arguments:
            inst_torque: float, the instantaneous torque setpoint in Nm. This is the torque from
                                the four-point-spline assistance generator which will dictate the
                                assistance, which follows a cubic spline profile.
        Returns:
            des_current: int, the desired current setpoint in mA.
        """
        pass

    # TODO: Add method to home the exos at standing angle
