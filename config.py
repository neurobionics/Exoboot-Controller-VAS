# Configuration and Constants file

######### PARAMS TO MODIFY PRIOR TO EACH VAS SESSION ######### 
# gRPC ip addresses (run in the following order: rtplot, then GUI client, then VAS_MAIN() script)
server_ip = f"{'35.3.134.250'}:" f"{'50051'}"   # IP address of the Controller (rPi)

# client_ip = f"{'0.0.0.0'}:" f"{'50051'}"         # IP address of Tablet (or my laptop if debugging) running the GUI
rtplot_ip = '35.3.80.31'    # ip address of server for real time ploting (monitor)
Vicon_ip_address='141.212.77.30'    # Vicon ip to connect to Bertec Forceplates for streaming
##############################################################  

# setting trial naming (components compiled into a full filename in GSE Thread)
subject_ID: str = "0"
trial_type: str = ""
trial_presentation: str = ""

# Variables UPDATED by GUI thread (for VAS Trial Type ONLY)
GUI_commanded_torque: float = 0.0   # Current Torque Experienced (Nm)
adjusted_slider_btn: str = 'nan'    # Adjusted Slider Btn
adjusted_slider_value: float = 0.0  # Adjusted Slider Value($)
confirm_btn_pressed: str = 'False'  # Confirm Button Pressed?
max_Vickrey_torque : float = 40.0   # Nm

# TOGGLES:
in_torque_FSM_mode: bool = True       # Toggle for 4pt FSM-based Torque Control or biomimetic Torque Control
bertec_fp_streaming: bool = True      # Toggle for Bertec Forceplate Streaming or IMU-based Gait State Estimation

## ~ Timing Parameters for the 4-Point Spline ~ ##

# # VARUN'S PREF STUDY PARAMS LOADED FOR FLAT WALKING AT 1.20m/s:
# t_rise = 27.9		# stance from t_peak
# t_peak = 53.3     # stance from heel strike
# t_fall = 10	    # stance from t_peak
# t_toe_off = 65    # stance from heel strike

# Incline Walking:
t_rise = 15		    # stance from t_peak
t_peak = 54		    # stance from heel strike
t_fall = 12		    # stance from t_peak
t_toe_off = 67		# stance from heel strike

# t_rise = 13		    # % stride from t_peak
# t_peak = 54		    # % stride from heel strike
# t_fall = 10		    # % stride from t_peak
# t_toe_off = 65		# % stride from heel strike

END_OF_STANCE = t_toe_off
END_OF_STRIDE = 100

holding_torque = 2	# Nm
spline_timing_params = [t_rise, t_peak, t_fall, t_toe_off, holding_torque]
max_dorsiflexed_ang_left = 0
max_dorsiflexed_ang_right = 0
output_torque = 0

# Basic Exo functionality constants/gains
RIGHT_EXO_DEV_IDS = [77, 17584]  # for EB-51
LEFT_EXO_DEV_IDS = [888, 48390]  # for EB-51
ENC_CLICKS_TO_DEG = 1 / (2**14 / 360)
BAUD_RATE: int =  230400
MAX_ALLOWABLE_CURRENT:int = 27000   #mA 
EXIT_MAIN_LOOP_FLAG = False
ANK_ENC_SIGN_RIGHT_EXO = -1
ANK_ENC_SIGN_LEFT_EXO = 1
N_left: float = 0
N_right: float = 0

DEFAULT_KP = 40
DEFAULT_KI = 400
DEFAULT_KD = 0
DEFAULT_FF = 128  # 128 is 100% feedforward

# Inferred from https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/ 
# Link:https://github.com/kriswiner/MPU6050/blob/master/MPU6050BasicExample.ino#L364
# ALSO on Dephy FlexSea Website
ACCEL_GAIN = 1 / 8192  # LSB -> gs
# Inferred from https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/ 
# Link: https://github.com/kriswiner/MPU6050/blob/master/MPU6050BasicExample.ino#L364
# ALSO on Dephy FlexSea Website
GYRO_GAIN = 1 / 32.75  # LSB -> deg/s

Kt = 0.000146 #mA/Nm
efficiency = 0.9    # 90% efficiency for belt drive

# Bertec Parameters
HS_THRESHOLD = 80
TO_THRESHOLD = 30

# Logging and Data variables
state_time_left: float = 0.0
temperature_left: float = 0.0

ankle_angle_left: float = 0.0
ankle_angle_right: float = 0.0

ankle_velocity_left: float = 0.0
ankle_velocity_right: float = 0.0

accel_x_left: float = 0.0
accel_y_left: float = 0.0
accel_z_left: float = 0.0

gyro_x_left: float = 0.0
gyro_y_left: float = 0.0
gyro_z_left: float = 0.0

motor_angle_left: float = 0.0
motor_velocity_left: float = 0.0
motor_current_left: float = 0.0

state_time_right: float = 0.0
temperature_right: float = 0.0

accel_x_right: float = 0.0
accel_y_right: float = 0.0
accel_z_right: float = 0.0

gyro_x_right: float = 0.0
gyro_y_right: float = 0.0
gyro_z_right: float = 0.0

motor_angle_right: float = 0.0
motor_velocity_right: float = 0.0
motor_current_right: float = 0.0

motor_angle_offset_left: float = 0.0
motor_angle_offset_right: float = 0.0

ankle_offset_left: float = 0.0
ankle_offset_right: float = 0.0

# Heel strike variables
heel_strike_left: int = 0
heel_strike_right: int = 0

stride_time_right: float = 1.0
stride_time_left: float = 1.0

time_in_current_stride_right: float = 0.0
time_in_current_stride_left: float = 0.0

# IMU Swing Variables
in_swing_start_left: bool = False
in_swing_start_right: bool = False
swing_val_left:float = 10
swing_val_right:float = 10

# Stance Time Variables
time_in_current_stance_left: float = 0.0
time_in_current_stance_right: float = 0.0
stance_time_left: float = 1.0
stance_time_right: float = 1.0

# Four-point spline torque
desired_spline_torque_left: float  = 0
desired_spline_torque_right: float = 0

# Back-calculated ankle torque
act_ank_torque_right: float = 0
act_ank_torque_left: float = 0

# Filter Vars
gyro_z_passband_freq: float = 1.0105 # Hz

# BERTEC variables:
z_forces_left = 0
z_forces_right = 0

HS_bool_right = False
HS_bool_left = False

bertec_HS_right = 0
bertec_HS_left = 0
in_swing_bertec_right = 0
in_swing_bertec_left = 0
swing_val_bertec_left = 0
swing_val_bertec_right = 0

stride_period_bertec_left = 0
stride_period_bertec_right = 0

time_in_current_stance_left = 0
time_in_current_stance_right = 0

# Thread Period Tracking
vas_main_frequency: float = 400
gui_communication_thread_frequency: float = 0
gse_thread_frequency: float = 0
bertec_thread_frequency: float = 0
vas_main_period: float = 0
gui_communication_thread_period: float = 0
gse_thread_period: float = 0
bertec_thread_period: float = 0 
