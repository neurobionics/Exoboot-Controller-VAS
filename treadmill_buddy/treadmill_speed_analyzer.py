import sys, csv, time, threading

sys.path.insert(0, '/home/pi/Exoboot-Controller-VAS/')
sys.path.insert(0, '/home/pi/Exoboot-Controller-VAS/Reference_Scripts_Bertec_Sync')

from SoftRTloop import FlexibleSleeper
from BertecMan import Bertec
from ZMQ_PubSub import Subscriber
from GroundContact import BertecEstimator

from constants import VICON_IP, BERTEC_ACC_RIGHT, BERTEC_ACC_LEFT

class TreadmillBuddy:
    def __init__(self):
        print("Starting TreadmillBuddy")
        self.subject_name = input("Subject name: ")
        self.fp_fname = self.subject_name + '_fpdata.csv'
        self.vals_fname = self.subject_name + '_vf_vals.csv'

        with open(self.fp_fname, 'w') as f:
            writer = csv.writer(f, delimiter=',', quotechar='|')
            writer.writerow(['pitime', 'HS_l', 'HS_r', 'fp_l', 'fp_r'])

        self.bertec = Bertec()
        self.bertec.start()

        self.sub_bertec_right = Subscriber(publisher_ip=VICON_IP, topic_filter='fz_right', timeout_ms=5)
        self.sub_bertec_left = Subscriber(publisher_ip=VICON_IP, topic_filter='fz_left', timeout_ms=5)
        self.bertec_estimator = BertecEstimator(self.sub_bertec_left, self.sub_bertec_right, filter_size=10)  

    def target_v_from_spm(self, v1, f1, f2):
        return f2**2/f1**2 * v1

    def run(self):
        v_ss = float(input("Set self selected speed: "))
        self.bertec.write_command(v_ss, v_ss, incline=None, accR=0.5, accL=0.5)

        target_f = 105.0 # Steps per minute (spm); Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5387837/#B16
        try:
            srt = FlexibleSleeper(1/500)
            start_time = time.perf_counter()
            cur_time = time.perf_counter()
            total_steps = 0
            with open(self.fp_fname, 'a') as f:
                writer = csv.writer(f, delimiter=',', quotechar='|')
                count = 0
                while cur_time - start_time < 60:
                    cur_time = time.perf_counter()
                    new_stride_flag_left, new_stride_flag_right, force_left, force_right = self.bertec_estimator.get_estimate()
                    writer.writerow([cur_time - start_time, new_stride_flag_left, new_stride_flag_right, force_left, force_right])

                    if new_stride_flag_left:
                        total_steps += 1
                    if new_stride_flag_right:
                        total_steps += 1

                    f = total_steps / (cur_time - start_time) * 60
                    v = self.bertec.speed   # m/s

                    if count > 2500:
                        count = 0
                        print("Treadmill Speed: ", v)
                        print("Steps Per Minute: ", f, '\n')
                    count += 1

                    srt.pause()

            f = total_steps / (cur_time - start_time) * 60
            v = self.bertec.speed   # m/s

            target_v = self.target_v_from_spm(v, f, target_f) # m/s
            print("Target SPM: {}".format(target_f))
            print("V to hit target SPM: {}".format(target_v))

            with open(self.vals_fname, 'w') as file:
                writer = csv.writer(file, delimiter=',', quotechar='|')
                writer.writerow(['pref_f', 'pref_v', 'target_f', 'target_v'])
                writer.writerow([f, v, target_f, target_v])

        except KeyboardInterrupt:
            print("KB interrupt. Exiting")

        finally:
            self.bertec.write_command(0, 0, incline=None, accR=BERTEC_ACC_RIGHT, accL=BERTEC_ACC_LEFT)
            self.bertec.stop()



if __name__ == "__main__":
    TreadmillBuddy().run()