"""
Collection of all the constants used throughout exoboot controller
"""


"""Static IP addresses"""
RTPLOT_IP = '35.3.80.31'    # ip address of server for real time ploting (monitor)
VICON_IP='141.212.77.30'    # Vicon ip to connect to Bertec Forceplates for streaming


"""File Paths on Pi"""
PORT_CFG_PATH = '/home/pi/VAS_exoboot_controller/ports.yaml' # DEPRECATED
TR_FOLDER_PATH = "Transmission_Ratio_Characterization"
SUBJECT_DATA_PATH = "subject_data"


"""TRIAL TYPES AND CONDITIONS"""
TRIAL_CONDS_DICT = {"VICKREY": {"COND": ["WNE", "EPO", "NPO"], "DESC": []},
                    "VAS": {"COND": [], "DESC": []},
                    "JND": {"COND": ["SPLITLEG", "SAMELEG"], "DESC": ["UNIFORM", "STAIR"]},
                    "PREF": {"COND": ["SLIDER", "BUTTON", "DIAL"], "DESC": []},
                    "ACCLIMATION": {"COND": [], "DESC": []},
                    "CONTROLPANEL": {"COND": [], "DESC": []}
                    }


"""LoggingNexus Fields for each thread"""
GENERAL_FIELDS = ['pitime', 'thread_freq']
GAIT_ESTIMATE_FIELDS = ['HS', 'current_time', 'stride_period', 'peak_torque', 'in_swing', 'N', 'torque_command', 'current_command']
SENSOR_FIELDS = ['state_time', 'temperature', 'winding_temp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y' ,'gyro_z',
            'ankle_angle', 'ankle_velocity', 'motor_angle', 'motor_velocity', 'motor_current', 'motor_voltage', 'battery_voltage', 'battery_current', 'act_ank_torque', 'forceplate']
BERTEC_FIELDS = ['forceplate_left', 'forceplate_right']
RTPLOT_FIELDS = ['pitime_left', 'pitime_right', 'motor_current_left', 'motor_current_right', 'batt_volt_left', 'batt_volt_right', 'case_temp_left', 'case_temp_right']

EXOTHREAD_FIELDS = GENERAL_FIELDS + GAIT_ESTIMATE_FIELDS + SENSOR_FIELDS
GSETHREAD_FIELDS = GENERAL_FIELDS + BERTEC_FIELDS

"""Transmission Ratio Constants"""
TR_FILE_PREFIX = "default_TR"
TR_COEFS_PREFIX = "{}_coefs".format(TR_FILE_PREFIX)
TR_FULLDATA_PREFIX = "{}_fulldata".format(TR_FILE_PREFIX)
TR_DATE_FORMATTER = "%Y_%m_%d_%H_%M"



"""Assistance Profile Constants"""
# Timing Parameters for the 4-Point Spline 

# Flat Walking (Varun's Pref Optimized Params for 1.20m/s)
# P_RISE = 27.9		# stance from t_peak
# P_PEAK = 53.3       # stance from heel strike
# P_FALL = 7	        # stance from t_peak
# P_TOE_OFF = 65		# stance from heel strike

# Incline Walking
P_RISE = 15		    # stance from p_peak
P_PEAK = 54		    # stance from heel strike
P_FALL = 12		    # stance from p_peak
P_TOE_OFF = 67		# stance from heel strike

END_OF_STANCE = P_TOE_OFF
END_OF_STRIDE = 100

HOLDING_TORQUE = 2	# 2 Nm
BIAS_CURRENT = 500 # 500 mA
SPINE_TIMING_PARAMS_DICT = {'P_RISE': P_RISE, 'P_PEAK': P_PEAK, 'P_FALL': P_FALL, 'P_TOE_OFF': P_TOE_OFF, 
                            'HOLDING_TORQUE': HOLDING_TORQUE, 'BIAS_CURRENT': BIAS_CURRENT}


"""Thermal Modelling Parameters"""
MAX_CASE_TEMP = 75 # Degree C
MAX_WINDING_TEMP = 110 # Degree C
TEMPANTISPIKE = 200 # Degree C


"""Exothread loop frequencies"""
FLEXSEA_FREQ = 1000 # Hz
EXOTHREAD_LOGGING_FREQ = 250 # Hz


"""Safety Limits"""
ZERO_CURRENT = 0 # mA
MAX_ALLOWABLE_CURRENT = 17000 # mA


"""Device Identifiers"""
# Exo Device IDS
RIGHT_EXO_DEV_IDS = [77, 17584]  # for EB-51
LEFT_EXO_DEV_IDS = [888, 48390, 1013]  # for EB-51
# Ankle encoder signs (plantar -> increasing angle)
ANK_ENC_SIGN_RIGHT_EXO = -1
ANK_ENC_SIGN_LEFT_EXO = 1
# Motor signs
MOTOR_SIGN_RIGHT = -1
MOTOR_SIGN_LEFT = -1
KNOWN_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1"]

# USE THESE DICTS
DEV_ID_TO_SIDE_DICT = {id: 'right' for id in RIGHT_EXO_DEV_IDS} | {id: 'left' for id in LEFT_EXO_DEV_IDS}
DEV_ID_TO_ANK_ENC_SIGN_DICT = {id: ANK_ENC_SIGN_RIGHT_EXO for id in RIGHT_EXO_DEV_IDS} | {id: ANK_ENC_SIGN_LEFT_EXO for id in LEFT_EXO_DEV_IDS}
DEV_ID_TO_MOTOR_SIGN_DICT = {id: MOTOR_SIGN_RIGHT for id in RIGHT_EXO_DEV_IDS} | {id: MOTOR_SIGN_LEFT for id in LEFT_EXO_DEV_IDS}


"""Device Attributes"""
# Unit Conversions (from Dephy Website, Units Section: https://dephy.com/start/#programmable_safety_features)
ENC_CLICKS_TO_DEG = 1 / (2**14 / 360)
BAUD_RATE: int =  230400
LOG_LEVEL: int = 3



"""Motor Attributes"""
Kt = 0.000146 #mA/Nm
EFFICIENCY = 0.9 # 90% efficiency for belt drive
RES_PHASE = 0.279 # Ohms
L_PHASE = 0.5 * 138 * 10e-6 # Henrys


"""Controller Gains"""
DEFAULT_KP = 40
DEFAULT_KI = 400
DEFAULT_KD = 0
DEFAULT_FF = 128  # 128 is 100% feedforward


"""IMU/GYRO Constants"""
# Inferred from https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/ 
# Link:https://github.com/kriswiner/MPU6050/blob/master/MPU6050BasicExample.ino#L364
# ALSO on Dephy FlexSea Website
ACCEL_GAIN = 1 / 8192  # LSB -> gs
# Inferred from https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/ 
# Link: https://github.com/kriswiner/MPU6050/blob/master/MPU6050BasicExample.ino#L364
# ALSO on Dephy FlexSea Website
GYRO_GAIN = 1 / 32.75  # LSB -> deg/s
#Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
ACCELX_SIGN = 1 #This is in the walking direction {i.e the rotational axis of the frontal plane}
ACCELY_SIGN = -1 # This is in the vertical direction {i.e the rotational axis of the transverse plane}
ACCELZ_SIGN = 1 # This is the rotational axis of the sagital plane

# Note based on the MPU reading script it says the gyro = radians(raw_gyro/gyroscale) for the gyrorange of 1000DPS the gyroscale is 32.8
GYROX_SIGN = -1
GYROY_SIGN = 1
GYROZ_SIGN = 1  # Remove -1 for EB-51


"""Filter Constants"""
GYROZ_W0: float = 1.0105 # Hz


"""Bertec Thresholds"""
HS_THRESHOLD = 80
TO_THRESHOLD = 30
ACCEPT_STRIDE_THRESHOLD = 0.2
ACCEPT_STANCE_THRESHOLD = 0.2

BERTEC_ACC_LEFT = 0.25
BERTEC_ACC_RIGHT = 0.25
