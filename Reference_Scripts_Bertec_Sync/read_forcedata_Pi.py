from ZMQ_PubSub import Subscriber 
import time
import numpy as np
from scipy.stats import norm
from GroundContact import GroundContact 

#set up osl frequency and Vicon information
Vicon_ip_address='141.212.77.30'

#set up subscriber channels 
sub_right = Subscriber(publisher_ip=Vicon_ip_address,topic_filter='fz_right',timeout_ms=5)
sub_left = Subscriber(publisher_ip=Vicon_ip_address,topic_filter='fz_left',timeout_ms=5)

#hs and to thresholds and variables to verify Bertec updates 
prev_z_right = 0
prev_z_left = 0

#variables to verify perturbations 
time_index_10 = 0
time_index_50 = 0
time_index_70 = 0

while True:
    right_stance_detector = GroundContact()            
    left_stance_detector = GroundContact()

    for t in osl.clock: 
        topic_right, z_forces_right, timestep_valid_right = sub_right.get_message()
        topic_left, z_forces_left, timestep_valid_left = sub_left.get_message()
        
        if z_forces_right == '':
            z_forces_right = prev_z_right  
        else:
            z_forces_right = float(z_forces_right)
        if z_forces_left == '':
            z_forces_left = prev_z_left 
        else: 
            z_forces_left = float(z_forces_left)

                                      
        right_stance_detector.update(z_forces_right, 'right')
        left_stance_detector.update(z_forces_left, 'left')
        
        prev_z_right = z_forces_right
        prev_z_left = z_forces_left
    