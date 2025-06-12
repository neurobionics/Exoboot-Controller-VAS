# Description:
# AssistanceGenerator creates a generic 4 point spline profile based on 4 parameters:
# rise time, peak torque time, fall time, and toe-off time.
#
# Profile is linearly scaled to fit profile to given max torque
#
# Profile saved as dict for fast lookup in terms of % stride
#
# Author: Nundini Rawal, John Hutchinson
# Date: 06/14/2024

import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scipy.interpolate import CubicSpline
from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging import Logger, LogLevel

from settings.constants import(
    INCLINE_WALK_TIMINGS,
    EXO_DEFAULT_CONFIG)

class AssistanceCalculator:
    def __init__(self,
                 t_rise:float=INCLINE_WALK_TIMINGS.P_RISE,
                 t_peak:float=INCLINE_WALK_TIMINGS.P_PEAK,
                 t_fall:float=INCLINE_WALK_TIMINGS.P_FALL,
                 holding_torque:float=EXO_DEFAULT_CONFIG.HOLDING_TORQUE,
                 resolution:int=10000)->None:

        if resolution <= 0:
            raise ValueError("Resolution must be greater than zero.")

        if t_rise < 0 or t_peak < 0 or t_fall < 0:
            raise ValueError("Timing parameters (t_rise, t_peak, t_fall) must be non-negative.")

        self.t_rise = t_rise       # % stance from t_peak
        self.t_peak = t_peak	   # % stance from heel strike
        self.t_fall = t_fall       # % stance from t_peak
        self.end_of_stride_in_percent = 100

        # convert timing params to percent stride
        self.convert_params_to_percent_stride()

        # determine torque onset & drop-off inflection pts
        self.calculate_onset_and_dropoff_times()

        self.holding_torque = holding_torque

        self.percent_stride = 0

        # normalized ranges
        self.normalize_min = 0
        self.normalize_max = 1
        self.resolution = resolution    # torque resolution of generic profile

        # determine rising and falling spline objects
        rising_spline, falling_spline = self.create_spline_sections()

        # create normalized profile
        self.create_normalized_profile(rising_spline, falling_spline)

    def set_new_timing_params(self, t_rise:float, t_peak:float, t_fall:float) -> None:
        """
        Set new timing parameters.

        Args:
            - t_rise (float): percent stance from t_peak
            - t_peak (float): percent stance from heel strike
            - t_fall (float): percent stance from t_peak
        """
        try:
            self.t_rise = t_rise
            self.t_peak = t_peak
            self.t_fall = t_fall
        except:
            raise Exception("set_new_timing_params failed in assistance generator")

    def set_new_holding_torque(self, holding_torque:float) -> None:
        """
        Set a new holding torque.

        Args:
            holding_torque: in Nm
        """
        self.holding_torque = holding_torque

    def create_spline_sections(self) -> tuple[object]:
        """
        Create rising and falling spline sections.
        """

        try:
            rising_spline = CubicSpline([self.t_onset, self.t_peak],
                                        [self.normalize_min, self.normalize_max],
                                        bc_type='clamped')

            falling_spline = CubicSpline([self.t_peak, self.t_dropoff],
                                         [self.normalize_max, self.normalize_min],
                                         bc_type='clamped')
        except Exception as err:
            raise ValueError(f"Failed to create CubicSpline for rising or falling section,"
                             "Error: {err}")

        return rising_spline, falling_spline

    def convert_params_to_percent_stride(self) -> None:
        """
        Convert timing parameters to percent stride
        """
        self.t_peak = self.t_peak / self.end_of_stride_in_percent
        self.t_rise = self.t_rise / self.end_of_stride_in_percent
        self.t_fall = self.t_fall / self.end_of_stride_in_percent

    def calculate_onset_and_dropoff_times(self) -> None:
        """
        Calculate torque onset time and torque drop-off time (in terms of % stride)
        """
        self.t_onset = self.t_peak - self.t_rise
        self.t_dropoff = self.t_peak + self.t_fall

        # check that dropoff is less than toe-off (in percent stride units)
        toe_off_percent = INCLINE_WALK_TIMINGS.P_TOE_OFF / self.end_of_stride_in_percent
        if self.t_dropoff >= toe_off_percent:
            raise ValueError("Drop-off time must be <= toe-off time; "
                             "Please change the fall time to be within toe-off bounds.")

    def create_normalized_profile(self, rising_spline:object, falling_spline:object) -> None:
        """
        Creates generic cubic spline based profile using loaded timing parameters ~
        (x-axis) percent range: [0, 1]
        (y-axis) torque range: [0, 1]

        A normalized_profile is saved as a dictionary attribute of this class.
        The dictionary is the size of the specified resolution, and can be indexed by
        integers from 0 to resolution size.

        This method NEEDS TO RUN BEFORE get_generic_torque_command() otherwise
        no profile will be loaded.

        Args:
            - rising_spline (obj): rising spline profile
            - falling_spline (obj): falling spline profile
        """

        normalized_profile = {}

        # for each idx, find % gait cycle & evaluate splines
        for idx in range(self.resolution):
            percent_gait = idx / self.resolution

            # Profile Conditions:
            if (percent_gait > 0) and (percent_gait <= self.t_onset):
                # Onset torque
                output_torque = self.normalize_min

            elif (percent_gait > self.t_onset) and (percent_gait <= self.t_peak):
                # Rising spline torque
                output_torque = rising_spline(percent_gait)

            elif (percent_gait > self.t_peak) and (percent_gait <= self.t_dropoff):
                # Falling spline torque
                output_torque =  falling_spline(percent_gait)

            else:
                output_torque = self.normalize_min

            # create a dictionary mapping each idx to an normalized torque value (between 0-1)
            normalized_profile[idx] = output_torque

        self.normalized_profile = normalized_profile

    def scale_to_peak_torque(self, normalized_torque:float, new_min_torque:float, new_peak_torque:float) -> float:
        """
        Linearly scales the normalized torque command to the desired peak torque setpoint.
        This method takes the normalized torque command (between 0 and 1) and scales it
        to the range defined by new_min_torque and new_peak_torque.

        Args:
            - normalized_torque (float): normalized torque command (between 0 and 1) based on current percent_stride
            - new_min_torque (float): minimum holding torque to maintain belt tension
            - new_peak_torque (float): desired peak torque setpoint to command

        Returns:
            - bounded_torque_command (float): scaled torque command to peak torque setpoint
        """

        input_torque_range = self.normalize_max - self.normalize_min    # between 0 and 1
        output_torque_range = new_peak_torque - new_min_torque          # between peak torque & holding torque

        # convert normalized torque setpoint to output torque range
        unbounded_torque_command = normalized_torque * (output_torque_range / input_torque_range)
        bounded_torque_command = unbounded_torque_command + new_min_torque  # ensure torque is larger than holding torque

        return bounded_torque_command

    def get_normalized_torque_command(self) -> float:
        """
        Evaluate normalized_profile at the current percent_stride.

        Converts the percent_stride to the nearest integer index.
        There is less error from int casting by increasing resolution.

        Returns:
            - normalized_torque_command (float): evaluated normalized profile at the idx
        """

        # find the idx corresponding to the % gait cycle
        idx = int(self.percent_stride * self.resolution)

        # ensure that idx doesn't exceed the specified resolution
        vetted_index = min(idx, self.resolution - 1)

        return float(self.normalized_profile[vetted_index])

    def torque_generator(self, current_time:float, stride_period:float, peak_torque:float, in_swing:bool) -> float:
        """
        Calculates torque command from normalized_profile.
        Scales this generic profile using the current gait state & peak torque setpoint.

        Args:
            - current_time (float): current time in stride (in seconds)
            - stride_period (float): latest stride period estimate (in seconds)
            - peak_torque (float): peak torque setpoint (specified by user)
            - in_swing (bool): flag indicating the leg is in swing phase
        """

        if in_swing:
            torque_command = self.holding_torque
        else:
            # Convert current time to percent stride
            self.percent_stride = current_time / stride_period

            # Get generic command
            normalized_torque_command = self.get_normalized_torque_command()

            # Scale command using given peak torque
            torque_command = self.scale_to_peak_torque(normalized_torque_command, self.holding_torque, peak_torque)

            # If torque_command is negative, raise ValueError and set to holding torque
            if torque_command < 0:
                raise ValueError(f"Negative torque command generated: {torque_command}. Setting to holding torque.")
                torque_command = self.holding_torque

        return torque_command

if __name__ == "__main__":

    # instantiate assistance generator
    assistance_generator = AssistanceCalculator()

    # instantiate the osl's softrt loop
    freq = 100  # Hz
    clock = SoftRealtimeLoop(dt=1/freq)

    peak_torque = input("peak torque to test (Nm): ")

    # initialize variables before logger tracks them
    stride_time = 1.2
    time_in_stride = 0.0
    in_swing_flag = False
    torque_command = 0.0

    # create a logger
    logger = Logger(log_path="assistance_calculator_test/",
                    file_name="test",
                    buffer_size=1000,
                    file_level=LogLevel.DEBUG,
                    stream_level=LogLevel.INFO
                )

    # track time, percent gait cycle and torque_command to a csv file
    logger.track_variable(lambda: time_in_stride, "time_in_stride_s")
    logger.track_variable(lambda: torque_command, "torque_setpt_Nm")
    logger.track_variable(lambda: assistance_generator.percent_stride, "percent_gait_cycle")
    logger.track_variable(lambda: in_swing_flag, "in_swing_flag_bool")

    for t in clock:
        try:
            # Update in_swing_flag based on percent_stride
            if assistance_generator.percent_stride > INCLINE_WALK_TIMINGS.P_TOE_OFF:
                in_swing_flag = True
            else:
                in_swing_flag = False

            # Simulate time in stride (in seconds)
            if time_in_stride >= stride_time:
                time_in_stride = 0.0
            else:
                time_in_stride += 1 / freq

            # acquire torque command based on gait estimate
            torque_command = assistance_generator.torque_generator(
                time_in_stride, stride_time, float(peak_torque), in_swing_flag)

            # update logger
            logger.update()

        except KeyboardInterrupt:
            logger.flush_buffer()
            logger.close()
            break

        except Exception as err:
            logger.flush_buffer()
            logger.close()
            break