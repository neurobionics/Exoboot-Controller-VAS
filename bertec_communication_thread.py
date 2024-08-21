import threading
from typing import Type

# logging from Bertec
import sys
import time
sys.path.insert(0, '/home/pi/VAS_exoboot_controller/Reference_Scripts_Bertec_Sync')
from ZMQ_PubSub import Subscriber 
from GroundContact import GroundContact 
import config

from utils import MovingAverageFilter

class Bertec(threading.Thread):
    def __init__(self, quit_event=Type[threading.Event], name='Bertec'):
        super().__init__(name=name)
        self.sub_bertec_right = Subscriber(publisher_ip=config.Vicon_ip_address,topic_filter='fz_right',timeout_ms=5)
        self.sub_bertec_left = Subscriber(publisher_ip=config.Vicon_ip_address,topic_filter='fz_left',timeout_ms=5)

        self.right_stance_detector = GroundContact()            
        self.left_stance_detector = GroundContact()
        self.prev_z_right = 0
        self.prev_z_left = 0
        
        self.quit_event = quit_event

        self.period_tracker = MovingAverageFilter(size = 500)
        
    def run(self):
        prev_end_time = time.time()
        while self.quit_event.is_set():
            # try:
            topic_right, z_forces_right, timestep_valid_right = self.sub_bertec_right.get_message()
            topic_left, z_forces_left, timestep_valid_left = self.sub_bertec_left.get_message()

            # Catching empty messages from ZmQ Bertec Streaming
            if z_forces_right == '':
                z_forces_right = self.prev_z_right  
            else:
                z_forces_right = float(z_forces_right)
            if z_forces_left == '':
                z_forces_left = self.prev_z_left 
            else: 
                z_forces_left = float(z_forces_left)
            
            config.z_forces_right = z_forces_right
            config.z_forces_left = z_forces_left
            
            # Heel Strike + Toe-off Detection and stance time computation 
            stance_time_right, HS_bool_right, time_in_current_stance_right, stride_period_bertec_right = self.right_stance_detector.update(z_forces_right)
            stance_time_left, HS_bool_left, time_in_current_stance_left, stride_period_bertec_left = self.left_stance_detector.update(z_forces_left)

            # print("For right side: stride_period is:",stride_period_bertec_right)
            # print("For right side: stance time is:",stance_time_right)
            # print("For right side: HS flag is:", HS_bool_right)
            # print("For right side: time in stance is:", time_in_current_stance_right)
            
            # Set config variables with stance times, time in current stance and stride time using Bertec data
            config.stance_time_left = stance_time_left
            config.stance_time_right = stance_time_right
            config.stride_period_bertec_right = stride_period_bertec_right
            config.stride_period_bertec_left = stride_period_bertec_left
            config.time_in_current_stance_left = time_in_current_stance_left
            config.time_in_current_stance_right = time_in_current_stance_right
            config.HS_bool_right = HS_bool_right
            config.HS_bool_left = HS_bool_left
            
            # right HS: 
            if HS_bool_right:
                config.bertec_HS_right = 10
                config.in_swing_bertec_right = False
                config.swing_val_bertec_right = 0
            else:
                config.bertec_HS_right = 0
                config.in_swing_bertec_right = True
                config.swing_val_bertec_right = 10
            
            # left HS:
            if HS_bool_left:
                config.bertec_HS_left = 10
                config.in_swing_bertec_left = False
                config.swing_val_bertec_left = 0
            else:
                config.bertec_HS_left = 0
                config.in_swing_bertec_left = True
                config.swing_val_bertec_left = 10
                
            # # Remove simulataneous forceplate activation by setting the in-swing flag
            # if HS_bool_right and HS_bool_left:
            #     config.in_swing_bertec_left = True
            #     config.swing_val_bertec_left = 100
                
            #     config.in_swing_bertec_right = True
            #     config.swing_val_bertec_right = 100
                
            self.prev_z_right = z_forces_right
            self.prev_z_left = z_forces_left
            
        # except:
        #     print("error in bertec communication thread!!!")
        #     self.quit_event.clear()

            # Update Period Tracker and config
            end_time = time.time()
            self.period_tracker.update(end_time - prev_end_time)
            prev_end_time = end_time
            config.bertec_thread_frequency = 1/self.period_tracker.average()
            