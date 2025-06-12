import time
from math import sqrt

class IMU_Estimator:
    def __init__(self, std_threshold = 2, run_len_threshold = 10, time_method = time.time):

        self.std_threhold = std_threshold
        self.run_len_threshold = run_len_threshold

        self.run_len = 0
        self.prev_accel = 0

        self.activation_state = False
        self.n = 0
        self.m = 0
        self.S = 1
        self.std = 1
        self.zscore = 0

        self.activation_state = False
        self.activations_pitime_local = 0
        self.activations_zscore_local = 0
        self.activations_pitime_start = []
        self.activations_zscore_start = []
        self.activations_pitime_peak = []
        self.activations_zscore_peak = []
        self.activations_status = []

        self.time_method = time_method

    def __repr__(self):
        rep_str = "{}, {}, {}, {}".format(self.activation_state, self.m, self.std, self.zscore)
        return rep_str

    def return_estimate(self):
        state_dict = {"activation": self.activation_state
                      }

        return state_dict

    def update(self, accel):
        diff = abs(accel - self.prev_accel)

        # Mean/STD real-time
        x = diff
        self.n = self.n + 1
        m_new = (self.m + (x - self.m))/self.n
        self.S = self.S + (x - m_new)*(x - self.m)

        self.std = sqrt(self.S/self.n)
        self.zscore = (x-m_new)/self.std

        # Track run length
        if self.zscore > self.std_threhold:
            self.run_len = 0
        else:
            self.run_len += 1

        # Activation Window
        if not self.activation_state and self.run_len <= self.run_len_threshold:
            self.activation_state = True
            self.activations_pitime_local = self.time_method()
            self.activations_zscore_local = self.zscore

            self.activations_pitime_start.append(self.activations_pitime_local)
            self.activations_zscore_start.append(self.activations_zscore_local)

        elif self.activation_state and self.run_len > self.run_len_threshold:
            self.activation_state = False
            self.activations_pitime_peak.append(self.activations_pitime_local)
            self.activations_zscore_peak.append(self.activations_zscore_local)

        elif self.activation_state and self.zscore > self.activations_zscore_local:
            self.activations_pitime_local = self.time_method()
            self.activations_zscore_local = self.zscore

        else:
            pass

        self.activations_status.append(self.activation_state)



if __name__ == "__main__":
    asdf = IMU_Estimator()
    print("INIT")
    print(asdf)

    for i in range(20):
        asdf.update(i)
        print(asdf)

    asdf.update(100)
    print(asdf)