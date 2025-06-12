import threading
import time
import numpy as np

class FlexibleSleeper():
    def __init__(self, clockperiod, history_size=50):
        self.clockperiod = clockperiod
        self.last_stop_time = time.perf_counter()

        self.period_history = np.zeros(history_size)
        self.history_pntr = 0

    def sleep(self):
        current_time = time.perf_counter()
        delay = max(self.clockperiod - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        self.last_stop_time = self.stop_time

    def sleepreturn(self):
        current_time = time.perf_counter()
        delay = max(self.clockperiod - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        period = self.stop_time - self.last_stop_time 
        self.last_stop_time = self.stop_time
        return period

class BaseThread:
    def __init__(self, clockperiod):
        self.clockperiod = clockperiod #ms
        self.sleeper = FlexibleSleeper(clockperiod)

        self.execution_flag = False

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True

    def start(self):
        self.execution_flag = True
        self.thread.start()

    def stop(self):
        self.execution_flag = False
        self.thread.join()

    def run(self):
        pass


class FastCollector(BaseThread):
    def __init__(self, clockperiod):
        super().__init__(clockperiod)
        self.val = 0

        self.prev_time = time.perf_counter()

        self.dt_len = 50
        self.dts = np.zeros(self.dt_len)
        self.pntr = 0

    def return_val(self):
        # random_execution_time = np.random.uniform(0.0, 0.001)
        # time.sleep(random_execution_time)
        return self.val
    
    def avg_runtime(self):
        return sum(self.dts)/self.dt_len
        # return self.start_time - self.prev_time

    def run(self):
        while self.execution_flag:
            # Start Main
            self.val += 1        
            # End Main

            self.dts[self.pntr] = self.sleeper.sleepreturn()
            self.pntr = (self.pntr + 1) % self.dt_len
            # while time.perf_counter() - start_time < self.clockperiod:
            #     pass


class Poker(BaseThread):
    def __init__(self, clockperiod, fastcollector):
        super().__init__(clockperiod)
        self.fastcollector = fastcollector

        self.prev_time = time.perf_counter()

    def poke(self, fc):
        return fc.return_val()

    def run(self):
        while self.execution_flag:
            # Start Main function
            num_pokes = np.random.randint(500, 10000)
            fc_val = 0
            for i in range(num_pokes):
                fc_val = self.poke(self.fastcollector)

            # End Main function

            # Sleep       
            period = self.sleeper.sleepreturn()
            # while time.perf_counter() - start_time < self.clockperiod:
            #     pass

            print("Poked FC {} times: {}".format(num_pokes, fc_val))
            print("FastCollector avg period: {}".format(self.fastcollector.avg_runtime()))
            # print("Execution time: {}".format(time.perf_counter() - start_time))
            print("Period: {}".format(period))
            print()


if __name__ == "__main__":
    fc = FastCollector(0.010)
    p = Poker(1.000, fc)

    fc.start()
    p.start()

    input()