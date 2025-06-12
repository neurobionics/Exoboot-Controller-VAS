"""
Collection of all the constants used throughout exoboot controller
"""

from .constants_dataclasses import (
    SPLINE_PARAMS,
    SIDE_SPECIFIC_EXO_IDENTIFIERS,
    EXO_MOTOR_CONSTANTS,
    EXO_SETUP_CONSTANTS,
    EXO_THERMAL_SAFETY_CONSTANTS,
    EXO_CURRENT_SAFETY_CONSTANTS,
    EXO_DEFAULT_CONSTANTS,
    EXO_PID_GAINS,
    IMU_CONSTANTS,
    BERTEC_THRESHOLDS,
    STATIC_IP_ADDRESSES
)

""" Static IP addresses """
IP_ADDRESSES = STATIC_IP_ADDRESSES(
    RTPLOT_IP = "35.3.69.66",
    VICON_IP = '141.212.77.30'
)

""" File Paths on Pi """
PORT_CFG_PATH = '/home/pi/VAS_exoboot_controller/ports.yaml' # DEPRECATED
SUBJECT_DATA_PATH = "subject_data"


""" TRIAL TYPES AND CONDITIONS """
TRIAL_CONDS_DICT = {"VICKREY": {"COND": ["WNE", "EPO", "NPO"], "DESC": []},
                    "VAS": {"COND": [], "DESC": []},
                    "JND": {"COND": ["SPLITLEG", "SAMELEG"], "DESC": ["UNIFORM", "STAIR"]},
                    }


""" Transmission Ratio Constants """
TR_FILE_PREFIX = "default_TR"
TR_COEFS_PREFIX = "{}_coefs".format(TR_FILE_PREFIX)
TR_FULLDATA_PREFIX = "{}_fulldata".format(TR_FILE_PREFIX)
TR_DATE_FORMATTER = "%Y_%m_%d_%H_%M"
TR_FOLDER_PATH = "./src/characterization/transmission_ratio_characterization/TR_coef_logs/"
TEST_TR_FILE = "default_TR_coefs_left_2025_02_04_16_13.csv"

# tuned for VAS study
INCLINE_WALK_TIMINGS = SPLINE_PARAMS(
    P_RISE=15,
    P_PEAK=54,
    P_FALL=12,
    P_TOE_OFF=67
)

# Varun's Pref Optimized Params for 1.20m/s:
FLAT_WALK_TIMINGS = SPLINE_PARAMS(
    P_RISE=27.9,
    P_PEAK=53.3,
    P_FALL=7,
    P_TOE_OFF=65
)

""" Device Identifiers """
KNOWN_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1"]

RIGHT_EXO_IDENTIFIERS = SIDE_SPECIFIC_EXO_IDENTIFIERS(
    EXO_DEV_IDS = [77, 17584, 1013],
    ANK_ENC_SIGN = -1,
    MOTOR_SIGN = -1
)

LEFT_EXO_IDENTIFIERS = SIDE_SPECIFIC_EXO_IDENTIFIERS(
    EXO_DEV_IDS = [888, 48390],
    ANK_ENC_SIGN = 1,
    MOTOR_SIGN = -1
)

DEV_ID_TO_SIDE_DICT = {id: 'right' for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS} | {id: 'left' for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS}
DEV_ID_TO_ANK_ENC_SIGN_DICT = {id: RIGHT_EXO_IDENTIFIERS.ANK_ENC_SIGN for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS} | {id: LEFT_EXO_IDENTIFIERS.ANK_ENC_SIGN for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS}
DEV_ID_TO_MOTOR_SIGN_DICT = {id: RIGHT_EXO_IDENTIFIERS.MOTOR_SIGN for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS} | {id: LEFT_EXO_IDENTIFIERS.MOTOR_SIGN for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS}

""" Device Attributes """
EB51_CONSTANTS = EXO_MOTOR_CONSTANTS(
    MOT_ENC_CLICKS_TO_REV = 2**14,
    MOT_ENC_CLICKS_TO_DEG = 360 / (2**14),
    Kt = 0.146, # in Nm/A
    EFFICIENCY = 0.9,
    RES_PHASE = 0.279,
    L_PHASE = 0.5 * 138 * 10e-6
)

""" Device Basic Setup & Communication Constants """
EXO_SETUP_CONST = EXO_SETUP_CONSTANTS(
    BAUD_RATE = 230400,
    FLEXSEA_FREQ = 500, # in Hz (REMINDER: ONLY CERTAIN FREQUENCIES SUPPORTED ~ 1000, 500)
    LOG_LEVEL = 3
)

""" Controller Gains """
DEFAULT_PID_GAINS = EXO_PID_GAINS(
    KP=40,
    KI=400,
    KD=0,
    FF=128
)

""" Thermal Parameters """
EXO_THERMAL_SAFETY_LIMITS = EXO_THERMAL_SAFETY_CONSTANTS(
    MAX_CASE_TEMP = 75,      # °C
    MAX_WINDING_TEMP = 110   # °C
)

""" Safety Limits """
EXO_CURRENT_SAFETY_LIMITS = EXO_CURRENT_SAFETY_CONSTANTS(
    ZERO_CURRENT = 0, # mA
    MAX_ALLOWABLE_CURRENT = 17000 # mA
    )

""" Default Configuration """
EXO_DEFAULT_CONFIG = EXO_DEFAULT_CONSTANTS(
    HOLDING_TORQUE = 2,  # in Nm
    BIAS_CURRENT = 500   # mA (not the same as transparent mode)
    )

""" IMU/GYRO Constants """
EXO_IMU_CONSTANTS = IMU_CONSTANTS(
    ACCEL_GAIN = 1 / 8192,      # note: osl DephyLegacyActuator uses m/s^2 instead of g's
    GYRO_GAIN = 1 / 32.75,      # note: osl DephyLegacyActuator uses rad/s instead of deg/s
    ACCELX_SIGN = 1,            # ALSO NOTE: ankle angles reported in deg*100
    ACCELY_SIGN = -1,
    ACCELZ_SIGN = 1,
    GYROX_SIGN = -1,
    GYROY_SIGN = 1,
    GYROZ_SIGN = 1
)

""" Bertec Thresholds """
BERTEC_THRESH = BERTEC_THRESHOLDS(
    HS_THRESHOLD = 80,
    TO_THRESHOLD = 30,
    ACCEPT_STRIDE_THRESHOLD = 0.2,
    ACCEPT_STANCE_THRESHOLD = 0.2,
    BERTEC_ACC_LEFT = 0.25,
    BERTEC_ACC_RIGHT = 0.25
)

""" Filtering Constants """
GYROZ_W0: float = 1.0105    # Hz
TEMPANTISPIKE = 100         # °C