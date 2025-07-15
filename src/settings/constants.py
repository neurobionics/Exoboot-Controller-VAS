"""
Collection of all the constants used throughout exoboot controller
"""

import time, pytz

from src.settings.constants_dataclasses import (
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
    STATIC_IP_ADDRESSES,
    EXO_THREAD_FREQUENCIES,
)

""" Static IP addresses """
# run rtplot with this command: python3 -m rtplot.server -p !!!INSERT CLIENT IP HERE!!!
IP_ADDRESSES = STATIC_IP_ADDRESSES(RTPLOT_IP="35.3.69.66", VICON_IP="141.212.77.30")


""" File Paths on Pi """
SUBJECT_DATA_PATH = "subject_data"


""" LoggingNexus Fields for each thread """
GENERAL_FIELDS = ["pitime", "thread_freq"]
# TODO: added HS and stride_period fields to GSE_IMU since ran into exception in logging nexus: dict contains fields not in fieldnames: 'HS', 'stride_period'
GSE_IMU_FIELDS = [
    "HS_imu",
    "current_time",
    "stride_period_imu",
    "in_swing_imu",
    "imu_activations",
    "peak_torque",
    "in_swing",
    "N",
    "torque_command",
    "current_command",
]
GAIT_ESTIMATE_FIELDS = [
    "HS",
    "current_time",
    "lag",
    "stride_period",
    "peak_torque",
    "in_swing",
    "N",
    "torque_command",
    "current_command",
]
SENSOR_FIELDS = [
    "state_time",
    "temperature",
    "winding_temp",
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "ankle_angle",
    "ankle_velocity",
    "motor_angle",
    "motor_velocity",
    "motor_current",
    "motor_voltage",
    "battery_voltage",
    "battery_current",
    "act_ank_torque",
    "forceplate",
]
BERTEC_FIELDS = ["forceplate_left", "forceplate_right"]
RTPLOT_FIELDS = [
    "pitime_left",
    "pitime_right",
    "motor_current_left",
    "motor_current_right",
    "batt_volt_left",
    "batt_volt_right",
    "case_temp_left",
    "case_temp_right",
]

# TODO: add enums/dataclass
COMBO_EXOTHREAD_FIELDS = (
    GENERAL_FIELDS + GSE_IMU_FIELDS + GAIT_ESTIMATE_FIELDS + SENSOR_FIELDS
)
IMU_EXOTHREAD_FIELDS = GENERAL_FIELDS + GSE_IMU_FIELDS + SENSOR_FIELDS
EXOTHREAD_FIELDS = GENERAL_FIELDS + GAIT_ESTIMATE_FIELDS + SENSOR_FIELDS
GSETHREAD_FIELDS = GENERAL_FIELDS + BERTEC_FIELDS


"""TRIAL TYPES AND CONDITIONS"""
TRIAL_CONDS_DICT = {
    "VICKREY": {"CONDITION1": ["WNE", "EPO", "NPO"]},
    "VAS": {},
    "JND": {"CONDITION1": ["SPLITLEG", "SAMELEG"], "CONDITION1": ["UNIFORM", "STAIR"]},
    "PREF": {"CONDITION1": ["SLIDER", "BUTTON", "DIAL"]},
    "ACCLIMATION": {"COND": ["SLIDER", "DIAL"]},
    "CONTROLPANEL": {},
}

""" Datetime Constants """
DETROIT_TIMEZONE = pytz.timezone('America/Detroit')
DATETIME_FORMATTER = "%Z_%Y_%m_%d_%H:%M:%S"
DATETIME_FORMATTER_LESS_SEC = "%Y_%m_%d_%H_%M"

""" Transmission Ratio Constants """
TR_FILE_PREFIX = "default_TR"
TR_COEFS_PREFIX = "{}_coefs".format(TR_FILE_PREFIX)
TR_FULLDATA_PREFIX = "{}_fulldata".format(TR_FILE_PREFIX)
TR_DATE_FORMATTER = "%Y_%m_%d_%H_%M"
TR_FOLDER_PATH = "./src/transmission_ratio/TR_coef_logs/"  # path to coeff logs


""" Assistance Timing """
# tuned for VAS study
INCLINE_WALK_TIMINGS = SPLINE_PARAMS(P_RISE=15, P_PEAK=54, P_FALL=10, P_TOE_OFF=67)


# Varun's Pref Optimized Params for 1.20m/s:
FLAT_WALK_TIMINGS = SPLINE_PARAMS(P_RISE=27.9, P_PEAK=53.3, P_FALL=10, P_TOE_OFF=65)


""" Assistance Type """
CONTINUOUS_MODE_FLAG = True # if true, peak torque commands will update mid-stride for instant feedback


""" Device Identifiers """
KNOWN_USB_SERIAL_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1"]

RIGHT_EXO_IDENTIFIERS = SIDE_SPECIFIC_EXO_IDENTIFIERS(
    EXO_DEV_IDS=[77, 17584, 1013], ANK_ENC_SIGN=-1, MOTOR_SIGN=-1
)

LEFT_EXO_IDENTIFIERS = SIDE_SPECIFIC_EXO_IDENTIFIERS(
    EXO_DEV_IDS=[888, 48390], ANK_ENC_SIGN=1, MOTOR_SIGN=-1
)

DEV_ID_TO_SIDE_DICT = {id: "right" for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS} | {
    id: "left" for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS
}

DEV_ID_TO_ANK_ENC_SIGN_DICT = {
    id: RIGHT_EXO_IDENTIFIERS.ANK_ENC_SIGN for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS
} | {id: LEFT_EXO_IDENTIFIERS.ANK_ENC_SIGN for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS}

DEV_ID_TO_MOTOR_SIGN_DICT = {
    id: RIGHT_EXO_IDENTIFIERS.MOTOR_SIGN for id in RIGHT_EXO_IDENTIFIERS.EXO_DEV_IDS
} | {id: LEFT_EXO_IDENTIFIERS.MOTOR_SIGN for id in LEFT_EXO_IDENTIFIERS.EXO_DEV_IDS}


""" Device Attributes """
EB51_CONSTANTS = EXO_MOTOR_CONSTANTS(
    MOT_ENC_CLICKS_TO_REV=2**14,
    MOT_ENC_CLICKS_TO_DEG=360 / (2**14),
    Kt=0.000146,    # in mA/Nm
    EFFICIENCY=0.9,
    RES_PHASE=0.279,
    L_PHASE=0.5 * 138 * 10e-6,
)


""" Device Basic Setup & Communication Constants """
EXO_SETUP_CONST = EXO_SETUP_CONSTANTS(
    BAUD_RATE=230400,
    FLEXSEA_FREQ=1000,  # in Hz (REMINDER: ONLY CERTAIN FREQUENCIES SUPPORTED ~ 1000, 500)
    LOG_LEVEL=3,
)

""" Exothread loop frequencies """
THREAD_FREQS = EXO_THREAD_FREQUENCIES(EXOTHREAD_FREQ=500, BERTEC_FREQ=250, LOGGING_FREQ=250)  # Hz


""" Controller Gains """
DEFAULT_PID_GAINS = EXO_PID_GAINS(KP=40, KI=400, KD=0, FF=128)


""" Thermal Parameters """
EXO_THERMAL_SAFETY_LIMITS = EXO_THERMAL_SAFETY_CONSTANTS(
    MAX_CASE_TEMP=75, MAX_WINDING_TEMP=110  # °C  # °C
)


""" Safety Limits """
EXO_CURRENT_SAFETY_LIMITS = EXO_CURRENT_SAFETY_CONSTANTS(
    ZERO_CURRENT=0, MAX_ALLOWABLE_CURRENT=26500  # mA
)


""" Default Configuration """
EXO_DEFAULT_CONFIG = EXO_DEFAULT_CONSTANTS(
    HOLDING_TORQUE=2, BIAS_CURRENT=750  # in Nm  # mA (not the same as transparent mode)
)


""" IMU/GYRO Constants """
EXO_IMU_CONSTANTS = IMU_CONSTANTS(
    ACCEL_GAIN=1 / 8192,  # note: LSB in g's
    GYRO_GAIN=1 / 32.75,  # note: LSB in deg/s
    ACCELX_SIGN=1,  # ALSO NOTE: ankle angles reported in enc counts, not deg*100
    ACCELY_SIGN=-1,
    ACCELZ_SIGN=1,
    GYROX_SIGN=-1,
    GYROY_SIGN=1,
    GYROZ_SIGN=1,
)


""" Bertec Thresholds """
BERTEC_THRESH = BERTEC_THRESHOLDS(
    HS_THRESHOLD=80,
    TO_THRESHOLD=30,
    ACCEPT_STRIDE_THRESHOLD=1.0,
    BERTEC_ACC_LEFT=0.25,
    BERTEC_ACC_RIGHT=0.25,
)


""" Filtering Constants """
TEMPANTISPIKE = 100  # °C


""" Gait State Estimation Toggle"""
GSE_MODE = "IMU"  # Options: "IMU", "BERTEC", "COMBO"


""" STANDARDIZING TIME"""
TIME_METHOD = time.perf_counter
