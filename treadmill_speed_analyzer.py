import threading

from utils import PID
from BertecMan import Bertec
from ZMQ_PubSub import Subscriber
from GroundContact import BertecEstimator

from constants import VICON_IP

class TreadmillBuddy:
    def __init__(self, Kp, Kd, Ki):
        print("Starting TreadmillBuddy")
        self.bertec = Bertec()
        self.bertec.start()

        self.sub_bertec_right = Subscriber(publisher_ip=VICON_IP, topic_filter='fz_right', timeout_ms=5)
        self.sub_bertec_left = Subscriber(publisher_ip=VICON_IP, topic_filter='fz_left', timeout_ms=5)
        self.bertec_estimator = BertecEstimator(self.sub_bertec_left, self.sub_bertec_right, filter_size=10)

        self.pid = PID()        

    def run(self):
        target_spm = 100.0
        try:
            taskcomplete = False
            while not taskcomplete:
                new_stride_flag_left, new_stride_flag_right, force_left, force_right = self.bertec_estimator.get_estimate()
                
                if new_stride_flag_left or new_stride_flag_right:
                    steps_per_min = self.bertec_estimator.return_steps_per_min()
                    error = steps_per_min - target_spm
        except KeyboardInterrupt:
            print("KB interrupt. Exiting")

            self.bertec.write_command(0, 0, incline=None, accR=BERTEC_ACC_RIGHT, accL=BERTEC_ACC_LEFT)
            self.bertec.stop()
