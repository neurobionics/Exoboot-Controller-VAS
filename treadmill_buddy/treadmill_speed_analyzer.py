import sys, csv, time, threading

sys.path.insert(1, '/home/pi/Exoboot-Controller-VAS/')
sys.path.insert(1, '/home/pi/Exoboot-Controller-VAS/Reference_Scripts_Bertec_Sync')

from SoftRTloop import FlexibleSleeper
from BertecMan import Bertec
from ZMQ_PubSub import Subscriber
from GroundContact import BertecEstimator

from constants import VICON_IP, BERTEC_ACC_RIGHT, BERTEC_ACC_LEFT

class TreadmillBase:
    def __init__(self, name='TreadmillBase'):
        self.name = name
        print("Starting {}".format(self.name))
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

    def clamp_v(self, v):
        """Clamp treamill speed [0, 2] m/s"""
        return min(max(v, 0), 2)

    def estimate_new_v(self, v1, f1, f2):
        """Walk Ratio invariance formula"""
        v2 = f2**2/f1**2 * v1
        return self.clamp_v(v2)

class TreadmillBuddyOptimizer(TreadmillBase):
    def __init__(self, walk_period=15):
        super().__init__(name='TreadmillBuddyOptimizer')
        self.walk_period = walk_period # s

    def run(self):
        v_set = self.clamp_v(float(input("Set initial speed: ")))

        f_target = 105.0 # Steps per minute (spm); Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5387837/#B16
        try:
            srt = FlexibleSleeper(1/500)

            IsOptimized = False
            with open(self.fp_fname, 'a') as f:
                writer = csv.writer(f, delimiter=',', quotechar='|')
                while not IsOptimized:
                    self.bertec.write_command(v_set, v_set, incline=None, accR=0.5, accL=0.5)

                    start_time = time.perf_counter()
                    cur_time = time.perf_counter()
                    total_steps = 0

                    # Collection time
                    while cur_time - start_time < self.walk_period:
                        cur_time = time.perf_counter()

                        # Update BertecEstimator using FP data
                        new_stride_flag_left, new_stride_flag_right, force_left, force_right = self.bertec_estimator.get_estimate()
                        writer.writerow([cur_time - start_time, new_stride_flag_left, new_stride_flag_right, force_left, force_right])

                        # Update step total
                        if new_stride_flag_left:
                            total_steps += 1
                        if new_stride_flag_right:
                            total_steps += 1

                        # Soft real-time
                        srt.pause()

                    # Get cadence/speed
                    f = total_steps / (cur_time - start_time) * 60 # spm
                    v = self.bertec.speed   # m/s

                    # Predict new v to reach spm criteria (105)
                    v_set = self.estimate_new_v(v, f, f_target)

                    # Finish if target is v_set is within 5% of target cadence
                    IsOptimized = abs((f - f_target)/f_target) < 0.01

                    print("Target Cadence: {}".format(f_target))
                    print("Observed Treadmill Speed: ", v)
                    print("Observed Cadence: ", f)
                    print("Next Treadmill Speed: {}".format(v_set))
                    print()

            print("Treadmill Optimizer Finished")
            print("Target Cadence: {}".format(f_target))
            print("Observed Cadence: ", f)
            print("Required Treadmill Speed: {}".format(v_set))
            print()

            with open(self.vals_fname, 'w') as file:
                writer = csv.writer(file, delimiter=',', quotechar='|')
                writer.writerow(['f_obs', 'v_obs', 'f_target', 'v_estimate'])
                writer.writerow([f, v, f_target, v_set])

        except KeyboardInterrupt:
            print("KB interrupt. Exiting")

        finally:
            print("Goodbye")
            self.bertec.write_command(0, 0, incline=None, accR=BERTEC_ACC_RIGHT, accL=BERTEC_ACC_LEFT)
            self.bertec.stop()

class TreadmillBuddy(TreadmillBase):
    def __init__(self):
        super().__init__(name='TreadmillBuddy')

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
    which = sys.argv[1]
    if which == 'o':
        TreadmillBuddyOptimizer(walk_period=20).run() 
    else:
        TreadmillBuddy().run()