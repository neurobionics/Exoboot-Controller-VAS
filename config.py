# setting trial naming (components compiled into a full filename in GSE Thread)
subject_ID: str = "0"
trial_type: str = ""
trial_presentation: str = ""

# Variables UPDATED by GUI thread (for VAS Trial Type ONLY)
GUI_commanded_torque: float = 0.0   # Current Torque Experienced (Nm)
adjusted_slider_btn: str = 'nan'    # Adjusted Slider Btn
adjusted_slider_value: float = 0.0  # Adjusted Slider Value($)
confirm_btn_pressed: str = 'False'  # Confirm Button Pressed?

max_dorsiflexed_ang_left = 0
max_dorsiflexed_ang_right = 0
output_torque = 0

EXIT_MAIN_LOOP_FLAG = False
in_torque_FSM_mode = True

N_left: float = 0
N_right: float = 0

# Data variables
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
vas_main_frequency: float = 0
gui_communication_thread_frequency: float = 0
gse_thread_frequency: float = 0
bertec_thread_frequency: float = 0
vas_main_period: float = 0
gui_communication_thread_period: float = 0
gse_thread_period: float = 0
bertec_thread_period: float = 0 


# Misc
t_rise: float = 0
t_peak: float = 0
t_fall: float = 0