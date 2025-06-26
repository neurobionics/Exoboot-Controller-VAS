import time
from math import sqrt
from utils import MovingAverageFilter
from constants import TIME_METHOD

INCLINE_HS_ANK_ANG_UPPER_BOUND = 55
INCLINE_HS_ANK_ANG_LOWER_BOUND = 30
FLAT_HS_ANK_ANG_UPPER_BOUND = 40
FLAT_HS_ANK_ANG_LOWER_BOUND = 20


class IMU_Estimator:
    """
    IMU_Estimator estimates activation events from onboard exoboot IMU acceleration data (z-axis)
    using real-time mean/std tracking and z-score thresholding.

    Outputs:
        - stride_period: time between two heel-strike activations
        - in_stance: flag that indicates that foot is in swing
        - HS_time: timestamp of most recent activation (heel strike)

    """

    def __init__(
        self,
        std_threshold: float = 2,
        run_len_threshold: int = 10,
        stride_period_init: float = 1.20,
        filter_size: int = 10,
    ):
        """
        Initialize the IMU_Estimator.

        Args:
            std_threshold (float): Z-score threshold for activation detection.
            run_len_threshold (int): Number of consecutive samples below threshold to end activation.
        """

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

        self.activations_pitime_local = 0
        self.activations_zscore_local = 0
        self.activations_pitime_start = []
        self.activations_zscore_start = []
        self.activations_pitime_peak = []
        self.activations_zscore_peak = []
        self.activations_status = []

        self.HS_time: float = TIME_METHOD()
        self.HS_time_prev: float = TIME_METHOD()
        self.in_stance: bool = False
        self.stride_period_tracker = MovingAverageFilter(
            initial_value=stride_period_init, size=filter_size
        )

    def __repr__(self):
        """
        Return a string representation of the estimator's current state.

        Returns:
            str: String summarizing activation state, mean, std, and z-score.
        """

        rep_str = "{}, {}, {}, {}".format(
            self.activation_state, self.m, self.std, self.zscore
        )
        return rep_str

    def return_estimate(self):
        """
        Return the current activation state as a dictionary.

        Returns:
            dict: Dictionary with the current activation state.
        """

        state_dict = {
            "HS_time": self.HS_time,
            "stride_period": self.stride_period_tracker.average(),
            "in_swing": not self.in_stance,
            "activation": self.activation_state,
        }

        return state_dict

    def update(self, accel: float, ank_ang: float):
        """
        Update the estimator with a new acceleration value, compute statistics,
        and manage activation state.

        Args:
            accel (float): The new z-acceleration value to process

        Returns:
            bool: The current activation state after update.
        """

        diff = abs(accel - self.prev_accel)

        # Mean/STD real-time
        x = diff
        self.n = self.n + 1
        m_new = (self.m + (x - self.m)) / self.n
        self.S = self.S + (x - m_new) * (x - self.m)

        self.std = sqrt(self.S / self.n)
        self.zscore = (x - m_new) / self.std

        # Track run length
        if self.zscore > self.std_threhold:
            self.run_len = 0
        else:
            self.run_len += 1

        # Activation Window
        if not self.activation_state and self.run_len <= self.run_len_threshold:
            self.activation_state = True
            self.activations_pitime_local = TIME_METHOD()
            self.activations_zscore_local = self.zscore

            self.activations_pitime_start.append(self.activations_pitime_local)
            self.activations_zscore_start.append(self.activations_zscore_local)

        elif self.activation_state and self.run_len > self.run_len_threshold:
            self.activation_state = False
            self.activations_pitime_peak.append(self.activations_pitime_local)
            self.activations_zscore_peak.append(self.activations_zscore_local)

        elif self.activation_state and self.zscore > self.activations_zscore_local:
            self.activations_pitime_local = TIME_METHOD()
            self.activations_zscore_local = self.zscore

        else:
            pass

        self.detect_which_gait_event(ank_ang)

    def detect_which_gait_event(self, ank_ang: float):
        """
        Detects gait event depending on activation state.

        Updates the last heel strike time, stride period and in_stance flag
        """

        if self.activation_state:
            # check if heel strike event
            if (self.in_stance == False) and (ank_ang > FLAT_HS_ANK_ANG_LOWER_BOUND) and (ank_ang < FLAT_HS_ANK_ANG_UPPER_BOUND):
                self.in_stance = True  # now in stance, i.e. heel strike just occured

                # get latest HS time
                self.HS_time = self.activations_pitime_local

                # get new stride period
                stride_period_new = self.HS_time - self.HS_time_prev

                # get averaged stride period
                stride_period_avg = self.stride_period_tracker.average()

                # only feed new stride period into moving average if it's reasonable
                if abs((stride_period_new - stride_period_avg) / stride_period_avg) < BERTEC_THRESH.ACCEPT_STRIDE_THRESHOLD: # TODO do when pause_event and updatefilters:
                    self.stride_period_tracker.update(stride_period_new)

                # update prev HS time to the latest time
                self.HS_time_prev = self.HS_time

            # check if toe-off event
            elif self.in_stance and (ank_ang > FLAT_HS_ANK_ANG_UPPER_BOUND):
                self.in_stance = False  # now in swing, i.e. toe-off just occured


if __name__ == "__main__":
    asdf = IMU_Estimator()
    print("INIT")
    print(asdf)

    for i in range(20):
        asdf.update(i, i + 20)
        asdf.return_estimate()
        print(asdf.return_estimate())

    asdf.update(100, 60)
    print(asdf)

    # test gse_imu with loaded .mat file
