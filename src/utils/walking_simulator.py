import time
import sys
import csv
import numpy as np

from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging import Logger, LogLevel

"""
How it works:
1. The WalkingSimulator class simulates a person walking with a fixed stride period.
2. It increments the current_time_in_stride at each update, until it resets to 0s at the stride period.
3. The update_time_in_stride method updates the current time in stride and resets it if it exceeds the stride period.
4. The update_ank_angle method calculates the ankle angle based on the current time in stride.
5. The time_in_stride_to_percent_GC method converts the time in stride to a percentage of the gait cycle.
6. The ankle angle trajectory is loaded from a CSV file, which contains the gait cycle (gc) and corresponding ankle angles (ank_ang).
"""

class WalkingSimulator():
    """
    Simulate a person walking with a variable stride period.
    Increments current_time_in_stride at each update, until it resets at the set stride period.
    Output looks like a sawtooth wave.
    Ankle angle trajectory is from Reznick et al. 2021 (10° uphill walking)

    Walker data is updated every milisecond.

    Args:
        stride_period (float): average stride time (in seconds)
    """

    def __init__(self, stride_period:float = 1.20):

        # simulation updates at fixed 1000 Hz frequency
        # i.e. it will increment walker state every millisecond
        self.sim_dt = 1.0 / 1000
        self._last_update_time = time.perf_counter()

        # start at heel strike (0% gait cycle and in stance)
        self.seed_stride_period = stride_period
        self.current_time_in_stride:float = 0
        self.stride_num:int = 0
        self.stride_start_time:float = time.perf_counter()

        self.current_percent_gait_cycle:float = 0.0
        self.in_swing_flag:bool = False

        # ankle angle trajectory from Reznick et al. 2021 (10° uphill walking)
        self._gc_traj = []
        self._ank_ang_traj = []

        try:
            with open('./src/utils/ankle_angle_trajectory.csv', 'r') as f:
                reader = csv.reader(f)

                for row in reader:
                    # skip the header
                    if row[0] == 1:
                        continue
                    else:
                        self._gc_traj.append(float(row[0]))
                        self._ank_ang_traj.append(float(row[1]))

        except Exception as err:
            print(f"Error when loading & parsing 'ankle_angle_trajectory.csv': {err}")
            print(err)
            sys.exit(1)

    def update(self) -> None:
        """
        This method updates the simulator state only if enough time
        has passed since the last update. If enough time hasn't passed,
        then it won't update the estimate.

        Main loop can update as often as it likes, but simulator will
        ONLY update at user-specified frequency specified at the init.

        """

        now = time.perf_counter()
        if now - self._last_update_time >= self.sim_dt:
            self._last_update_time += self.sim_dt

            _ = self.update_time_in_stride()
            _ = self.update_ank_angle()
            self.toggle_in_swing_flag()

    def update_time_in_stride(self)-> float:
        """
        Updates the gait state based on the current time in stride.
        """

        # before first stride, create stride_period attribute
        if self.stride_num < 1:
            self.stride_period = self.seed_stride_period

        if self.current_time_in_stride >= self.stride_period:
            self.current_time_in_stride = 0
            self.update_stride_period() # update stride period target

            self.stride_start_time = time.perf_counter()
            self.stride_num += 1
            print(f'{self.stride_num} stride(s) completed')

        elif self.current_time_in_stride < self.stride_period:
            self.current_time_in_stride = time.perf_counter() - self.stride_start_time
            print(f"time in curr stride: {self.current_time_in_stride:.3f}")

        return self.current_time_in_stride

    def update_stride_period(self):
        """
        Updates stride period target to mimic human walking variability.

        Randomly samples a stride period from a normal distribution
        centered at 1.2s, with a standard deviation of 0.4s.
        """

        self.stride_period = np.random.normal(loc=self.seed_stride_period, scale=0.2)

    def update_ank_angle(self)-> float:
        """
        Updates the ankle angle based on the current time in stride.
        """

        self.current_percent_gait_cycle = self.time_in_stride_to_percent_GC(self.current_time_in_stride)

        # interpolate angle at the current % gait cycle
        interp_ang_at_query_pt = np.interp(self.current_percent_gait_cycle, self._gc_traj, self._ank_ang_traj)

        return interp_ang_at_query_pt

    def time_in_stride_to_percent_GC(self, time_in_stride:float)-> float:
        """
        Converts the time in stride to a percentage of the gait cycle.
        """

        if time_in_stride < 0:
            raise ValueError("Time in stride cannot be negative.")
        elif time_in_stride > self.stride_period:
            self.current_percent_gait_cycle = 100
        else:
            self.current_percent_gait_cycle = time_in_stride / self.stride_period * 100

        print(f"percent GC: {self.current_percent_gait_cycle:.2f}")

        return self.current_percent_gait_cycle

    def set_percent_toe_off(self, percent_toe_off:float=67)->None:
        """
        Can use to set a percent toe-off-time if looking to get swing/stance flag output
        """

        self.percent_toe_off = percent_toe_off

    def toggle_in_swing_flag(self):
        """
        False if person is NOT in swing (i.e. stance), and
        True if person is in swing.

        Decides based on user-specified toe-off time.
        """

        if self.current_percent_gait_cycle >= self.percent_toe_off:
            self.in_swing_flag = True
        else:
            self.in_swing_flag = False

    def return_estimate(self):
        """
        Return a dictionary of the most recent state of estimator {a, b, c}
            a) most recent heel strike time
            b) average stride period
            c) in swing flag

        """

        state_dict = {"HS_time": self.stride_start_time,
                      "stride_period": self.stride_period,
                      "in_swing": self.in_swing_flag
                    }

        return state_dict


if __name__ == '__main__':

    walker = WalkingSimulator(stride_period=1.20)
    walker.set_percent_toe_off(67)

    freq = 100  # Hz
    clock = SoftRealtimeLoop(dt=1/freq)

    # create a logger
    logger = Logger(log_path="walking_sim_test/",
                    file_name="test",
                    buffer_size=1000,
                    file_level=LogLevel.DEBUG,
                    stream_level=LogLevel.INFO
                )

    # track time, percent gait cycle and torque_command to a csv file
    logger.track_variable(lambda: walker.current_time_in_stride, "time_in_stride_s")
    logger.track_variable(lambda: walker.current_percent_gait_cycle, "percent_gait_cycle")
    logger.track_variable(lambda: walker.in_swing_flag, "in_swing_flag_bool")

    for t in clock:
        try:
            # update walking sim
            walker.update()

            estimate = walker.return_estimate()
            print(estimate)

            # update logger
            logger.update()

        except KeyboardInterrupt:
            logger.flush_buffer()
            logger.close()
            break

        except Exception as err:
            logger.flush_buffer()
            logger.close()
            break