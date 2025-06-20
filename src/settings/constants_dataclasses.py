"""
Collection of data classes to support constants used throughout the exoboot controller
"""

from dataclasses import dataclass

@dataclass
class SESSION_INPUTS:
    """
    Class to define the experimental session details.

    Examples:
        >>> constants = SESSION_INPUTS(
        ...     SUBJECT_ID = AB10,          % ABX
        ...     TRIAL_TYPE = acclimation,   % VAS/Vickrey/Acclimation/JND/Pref
        ...     TRIAL_COND = slider,        % slider, dial, btn-type/trial/group (for VAS)
        ...     DESC = 67,                  % Usually the date in this format: MMDDYY (i.e. 01312025, which is Jan 31, 2025)
        ...     BACKUP = yes,               % specify if data should be pickled
        ...     FILENAME
        ...     START_STAMP = time.time()   % time at whichmain loop/program started
        ... )
        >>> print(SESSION_INPUTS.TRIAL_COND)
        slider
    """
    SUBJECT_ID:str
    TRIAL_TYPE:str
    TRIAL_CONDITION:str
    DESCRIPTION:str
    USE_BACKUP:str
    FILENAME:str
    START_STAMP:float

@dataclass
class SPLINE_PARAMS:
    """
    Class to define the four-point-spline assistance parameters.
    These are to be held constant.

    Examples:
        >>> constants = SPLINE_PARAMS(
        ...     P_RISE = 15,    % stance before peak torque timing
        ...     P_PEAK = 54,    % stance after heel strike timing (0%)
        ...     P_FALL = 12,    % stance after peak torque timing
        ...     P_TOE_OFF = 67, % stance after heel strike time (0%)
        ... )
        >>> print(constants.P_RISE)
        15
    """

    P_RISE:int
    P_PEAK:int
    P_FALL:int
    P_TOE_OFF:int

@dataclass
class SIDE_SPECIFIC_EXO_IDENTIFIERS:
    """
    Class to define the following side-specific constants that
    can also be used to ID the device side:
    (1) list of exo DEV_ID's
    (2) ankle encoder signage (where max plantarflexion is ~140°)
    (3) motor signage

    These are to be held constant.

    Examples:
        >>> right_exo_identifiers = SIDE_SPECIFIC_EXO_IDENTIFIERS(
        ...     EXO_DEV_IDS = [77, 17584, 1013],
        ...     ANK_ENC_SIGN = -1,
        ...     MOTOR_SIGN = -1,
        ... )
        >>> print(right_exo_identifiers.MOTOR_SIGN)
        -1
    """

    EXO_DEV_IDS:list[int]
    ANK_ENC_SIGN:int
    MOTOR_SIGN:int

@dataclass
class EXO_MOTOR_CONSTANTS:
    """
    Class to define the following motor constants:
    Several units are from the Dephy Website, Units Section: https://dephy.com/start/#programmable_safety_features

    (1) Motor encoder clicks to revolutions
    (2) Motor torque constant (kt in Nm/mA)
    (3) System efficiency (including belt drive compliance)
    (4) Phase resistance (in ohms)
    (5) Phase inductance (in henrys)

    These are to be held constant.

    Examples:
        >>> eb51constants = EXO_MOTOR_CONSTANTS(
        ...     MOT_ENC_CLICKS_TO_REV = 2**14,
        ...     MOT_ENC_CLICKS_TO_REV = 360/2**14,
        ...     Kt = 0.146,
        ...     EFFICIENCY = 0.8,
        ...     RES_PHASE = 0.279,
        ...     L_PHASE = 0.5 * 138 * 10e-6
        ... )
        >>> print(eb51constants.MOT_ENC_CLICKS_TO_REV)
        16384
    """
    MOT_ENC_CLICKS_TO_REV:int
    MOT_ENC_CLICKS_TO_DEG:float
    Kt:float
    EFFICIENCY:float
    RES_PHASE:float
    L_PHASE:float

@dataclass
class EXO_SETUP_CONSTANTS:
    """
    Class to define the following set-up constants for the exoboots.:

    (1) Baud Rate
    (2) Flexsea frequency (Hz) ~ this is the frequency at which the exoboots will run
    (3) Log Level ~ this is the level of logging that will be used in the exoboots

    These are to be held constant.

    Examples:
        >>> eb51const = EXO_SETUP_CONSTANTS(
        ...     BAUD_RATE = 230400,
        ...     FLEXSEA_FREQ = 1000,
        ...     LOG_LEVEL= 6,
        ... )
        >>> print(eb51const.LOG_LEVEL)
        6
    """
    BAUD_RATE:int
    FLEXSEA_FREQ:int
    LOG_LEVEL:int

@dataclass
class IMU_CONSTANTS:
    """
    Class to define IMU constants ~

    Inferred from:
    (a) https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/
    (b) https://github.com/kriswiner/MPU6050/blob/master/MPU6050BasicExample.ino#L364
    (c) Dephy Flexsea Website

    ** Note based on the MPU reading script:
    >>> accel = raw_accel/accel_scale * 9.80605,
    >>> so if the returned accel value is multiplied by
    >>> the gravity term, then the accel_scale for 4g is 8192

    ** Note based on the MPU reading script:
    >>> gyro = radians(raw_gyro/gyro_scale),
    >>> so for the gyrorange of 1000DPS the gyroscale is 32.8

    The constants are:
    (1) ACCEL_GAIN converts LSB -> g's
    (2) GYRO_GAIN converts LSB -> deg/s
    (3) Motor torque constant (kt in Nm/mA)
    (4) System efficiency (including belt drive compliance)
    (5) Phase resistance (in ohms)
    (6) Phase inductance (in henrys)

    These are to be held constant.

    Examples:
        >>> eb51_imu_constants = IMU_CONSTANTS(
        ...     ACCEL_GAIN = 1 / 8192,
        ...     GYRO_GAIN = 1 / 32.75,
        ...     ACCELX_SIGN = 1,    # This is in the walking direction {i.e the rotational axis of the frontal plane}
        ...     ACCELY_SIGN = -1,   # This is in the vertical direction {i.e the rotational axis of the transverse plane}
        ...     ACCELZ_SIGN = 1,    # This is the rotational axis of the sagital plane
        ...     GYROX_SIGN = -1
        ...     GYROY_SIGN = 1
        ...     GYROZ_SIGN = 1
        ... )
        >>> print(eb51constants.ACCEL_GAIN)
        0.00012207031
    """
    ACCEL_GAIN:float = 1 / 8192
    GYRO_GAIN:float = 1 / 32.75

    ACCELX_SIGN:int = 1
    ACCELY_SIGN:int = -1
    ACCELZ_SIGN:int = 1

    GYROX_SIGN:int = -1
    GYROY_SIGN:int = 1
    GYROZ_SIGN:int = 1

@dataclass
class BERTEC_THRESHOLDS:
    """
    Class to define any bertec thresholds to recognize swing/stance
    and to set bertec settings for remote control.

    These are to be held constant.

    Examples:
        >>> constants = BERTEC_THRESHOLDS(
        ...     HS_THRESHOLD = 15,    % threshold to detect heel strike (N)
        ...     TO_THRESHOLD = 50,    % threshold to detect toe off (N)
        ...     ACCEPT_STRIDE_THRESHOLD = 0.2,    % acceptable stride threshold (sec)
        ...     ACCEPT_STANCE_THRESHOLD = 0.2,    % acceptable stance threshold (sec)
        ...     BERTEC_ACC_LEFT = 0.2   % left tread acceleration
        ...     BERTEC_ACC_RIGHT = 0.2  % right tread acceleration
        ... )
        >>> print(constants.BERTEC_ACC_RIGHT)
        0.2
    """

    HS_THRESHOLD:int
    TO_THRESHOLD:int

    ACCEPT_STRIDE_THRESHOLD:float
    ACCEPT_STANCE_THRESHOLD:float

    BERTEC_ACC_LEFT:float
    BERTEC_ACC_RIGHT:float

@dataclass
class EXO_PID_GAINS:
    """
    Dataclass to hold PID controller gains and feedforward value.
    Optimal params from Dephy Website for current control.
    """
    KP: int
    KI: int
    KD: int
    FF: int

@dataclass
class EXO_CURRENT_SAFETY_CONSTANTS:
    """
    Class to define the current (mA) safety constants.
    These are to be held constant.
    """
    ZERO_CURRENT: int  # mA
    MAX_ALLOWABLE_CURRENT:int  # mA

@dataclass
class EXO_THERMAL_SAFETY_CONSTANTS:
    """
    Class to define the thermal safety constants.
    These are to be held constant.
    """
    MAX_CASE_TEMP:int      # °C
    MAX_WINDING_TEMP:int  # °C

@dataclass
class EXO_DEFAULT_CONSTANTS:
    """
    Class to define the defaults constants.
    These are to be held constant.
    """
    HOLDING_TORQUE: float # in Nm
    BIAS_CURRENT: int # mA (not the same as transparent mode)

@dataclass
class STATIC_IP_ADDRESSES:
    """
    Dataclass to hold static IP addresses for exoboot system components.
    RTPLOT_IP: ip address of server for real time plotting (monitor) --
        rtplot command in server terminal:
            python3 -m rtplot.server -p 35.3.249.99
    VICON_IP: Vicon ip to connect to Bertec Forceplates for streaming
    """
    RTPLOT_IP: str
    VICON_IP: str