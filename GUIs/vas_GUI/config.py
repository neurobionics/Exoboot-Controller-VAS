# This file contains all the global variables that are used throughout the GUI and the Exo communication

import numpy as np

###### FOR TEST SERVER TESTING  ######
server_ip = f"{'0.0.0.0'}:" f"{'50051'}"   # IP address when just testing on same machine
client_ip = f"{'0.0.0.0'}:" f"{'50051'}"   # IP address when just testing on same machine
gui_commanded_torque: float = 0.0          # For TestServer_2.py 
grpc_needed:bool = True                    # SET TO FALSE IF DOING GUI TESTING W/O COMMANDING EXO

###### INITIALIZING RELEVANT VARS  ######
bool_confirm_button_pressed: bool = False
starting_val:int = 0         # Initial value of the slider cursor

##################################################
###### MODIFY THESE VALUES FOR EACH SUBJECT ######
##################################################

GUI_btn_setup:str = '4btn'                              # Full 12 btn setup or 4 btn setup ('full' or '4btn')
sub_num:int = 1
curr_trial_num:int = 1                                  # Current trial number (out of 4 if '4btn' setup and 3 if 'full' setup)
current_presentation_num:int = 1                        # Only 1 presentation if 'full' setup and 3 presentations if '4btn' setup

NPO_MV:float = -18.60        # Value of the slider at the extreme negative end (REMEMBER TO CHANGE IN .KV FILE)
EPO_MV:float = 3.4           # Value of the slider at the extreme positive end (REMEMBER TO CHANGE IN .KV FILE)


###### FOR EXO GRPC COMMUNICATION ######
# server_ip = f"{'35.3.134.250'}:" f"{'50051'}"   # IP address of the Controller (rPi)


# Setting up Torque options
min_torque:float = 0.0                                  # Minimum torque value
max_torque:float = 30.0                                 # Maximum torque value
num_of_tot_torque_settings:int = 12                     # Total number of torque settings (Maintain 12 for practicality)
torque_step:float = (max_torque - min_torque)/num_of_tot_torque_settings  # Step size for the torque buttons (maintain 12 btns)
torque_settings = np.arange(torque_step,max_torque+torque_step,torque_step)  # All Torque settings (np.arrange doesn't include stop value)