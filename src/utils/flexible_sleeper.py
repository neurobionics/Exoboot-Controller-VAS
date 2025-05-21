import time 

class FlexibleSleeper():
    """
    Inactive timer using sleep by delay
    """
    def __init__(self, dt):
        self.period = dt
        self.last_stop_time = time.perf_counter()

    def pause(self):
        current_time = time.perf_counter()
        delay = max(self.period - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        self.last_stop_time = self.stop_time

    def pause_return(self):
        current_time = time.perf_counter()
        delay = max(self.period - (current_time - self.last_stop_time), 0)
        time.sleep(delay)
        self.stop_time = time.perf_counter()
        period = self.stop_time - self.last_stop_time 
        self.last_stop_time = self.stop_time
        
        return period