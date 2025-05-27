"""
Collection of all the constants used throughout exoboot controller
"""
from dataclasses import dataclass

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
    
    # TODO: add a check to make sure that p_peak + p_fall is less than p_toe_off  
    
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
    (2) Baude rate
    (3) Motor torque constant (kt in Nm/mA)
    (4) System efficiency (including belt drive compliance)
    (5) Phase resistance (in ohms)
    (6) Phase inductance (in henrys)
    
    These are to be held constant.

    Examples:
        >>> eb51constants = EXO_MOTOR_CONSTANTS(
        ...     MOT_ENC_CLICKS_TO_REV = 2**14,    
        ...     MOT_ENC_CLICKS_TO_REV = 360/2**14, 
        ...     BAUD_RATE = 230400,  
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
    BAUD_RATE:int
    Kt:float              
    EFFICIENCY:float           
    RES_PHASE:float       
    L_PHASE:float
    
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


""" Static IP addresses """
RTPLOT_IP = "35.3.69.66"        # ip address of server for real time ploting (monitor) -- rtplot command in server terminal: python3 -m rtplot.server -p 35.3.249.99
VICON_IP = '141.212.77.30'      # Vicon ip to connect to Bertec Forceplates for streaming


""" File Paths on Pi """
PORT_CFG_PATH = '/home/pi/VAS_exoboot_controller/ports.yaml' # DEPRECATED
SUBJECT_DATA_PATH = "subject_data"


""" TRIAL TYPES AND CONDITIONS """
TRIAL_CONDS_DICT = {"VICKREY": {"COND": ["WNE", "EPO", "NPO"], "DESC": []},
                    "VAS": {"COND": [], "DESC": []},
                    "JND": {"COND": ["SPLITLEG", "SAMELEG"], "DESC": ["UNIFORM", "STAIR"]},
                    "PREF": {"COND": ["SLIDER", "BUTTON", "DIAL"], "DESC": []},
                    "ACCLIMATION": {"COND": [], "DESC": []},
                    "CONTROLPANEL": {"COND": [], "DESC": []}
                    }


""" LoggingNexus Fields for each thread """
GENERAL_FIELDS = ['pitime', 'thread_freq']
GAIT_ESTIMATE_FIELDS = ['HS', 'current_time', 'stride_period', 'peak_torque', 'in_swing', 'N', 'torque_command', 'current_command']
SENSOR_FIELDS = ['state_time', 'temperature', 'winding_temp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y' ,'gyro_z',
            'ankle_angle', 'ankle_velocity', 'motor_angle', 'motor_velocity', 'motor_current', 'motor_voltage', 'battery_voltage', 'battery_current', 'act_ank_torque', 'forceplate']
BERTEC_FIELDS = ['forceplate_left', 'forceplate_right']
RTPLOT_FIELDS = ['pitime_left', 'pitime_right', 'motor_current_left', 'motor_current_right', 'batt_volt_left', 'batt_volt_right', 'case_temp_left', 'case_temp_right']

EXOTHREAD_FIELDS = GENERAL_FIELDS + GAIT_ESTIMATE_FIELDS + SENSOR_FIELDS
GSETHREAD_FIELDS = GENERAL_FIELDS + BERTEC_FIELDS


""" Transmission Ratio Constants """
TR_FILE_PREFIX = "default_TR"
TR_COEFS_PREFIX = "{}_coefs".format(TR_FILE_PREFIX)
TR_FULLDATA_PREFIX = "{}_fulldata".format(TR_FILE_PREFIX)
TR_DATE_FORMATTER = "%Y_%m_%d_%H_%M"
TR_FOLDER_PATH = "./src/characterization/transmission_ratio_characterization/TR_coef_logs/"
TEST_TR_FILE = "default_TR_coefs_left_2025_02_04_16_13.csv"


""" Assistance Profile Constants """
HOLDING_TORQUE = 2	# Nm
BIAS_CURRENT = 500  # mA

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

""" Thermal Parameters """
MAX_CASE_TEMP = 75      # °C
MAX_WINDING_TEMP = 110  # °C
TEMPANTISPIKE = 100     # °C


""" Exothread loop frequencies """
FLEXSEA_FREQ = 1000 # Hz
EXOTHREAD_LOGGING_FREQ = 250 # Hz


""" Safety Limits """
ZERO_CURRENT = 0 # mA
MAX_ALLOWABLE_CURRENT = 17000 # mA


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
    BAUD_RATE = 230400,
    Kt = 0.000146,              
    EFFICIENCY = 0.9,            
    RES_PHASE = 0.279,          
    L_PHASE = 0.5 * 138 * 10e-6 
)

LOG_LEVEL:int = 3


""" Controller Gains """
DEFAULT_KP = 40
DEFAULT_KI = 400
DEFAULT_KD = 0
DEFAULT_FF = 128    # 128 is 100% feedforward


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


""" Filter Constants """
GYROZ_W0: float = 1.0105    # Hz


""" Bertec Thresholds """
BERTEC_THRESH = BERTEC_THRESHOLDS(
    HS_THRESHOLD = 80,
    TO_THRESHOLD = 30,
    ACCEPT_STRIDE_THRESHOLD = 0.2,
    ACCEPT_STANCE_THRESHOLD = 0.2,
    BERTEC_ACC_LEFT = 0.25,
    BERTEC_ACC_RIGHT = 0.25 
)
