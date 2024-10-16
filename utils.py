import os

class subject_data_filing_cabinet:
    """
    Class to create subject_data folder and subject subfolders
    """
    def __init__(self, subject):
        self.subject = subject
        self.subject_path = ""

        if not os.path.isdir("subject_data"):
            os.mkdir("subject_data")
        self.subject_path = os.path.join(self.subject_path, "subject_data")
        
        if not os.path.isdir(os.path.join(self.subject_path, self.subject)):
            os.mkdir(os.path.join(self.subject_path, self.subject))
        self.subject_path = os.path.join(self.subject_path, self.subject)

    def getpath(self):
        return self.subject_path


class MovingAverageFilter:
    """
    Use to track averages of some numerical quantity
    """
    def __init__(self, initial_value:float = 0, size:int = 5):
        self.size = size
        self.buffer = [initial_value] * self.size
        self.pntr = 0

    def most_recent(self):
        return self.buffer[self.pntr - 1]

    def average(self):
        return sum(self.buffer) / self.size
    
    def update(self, val):
        self.buffer[self.pntr] = val
        self.pntr = (self.pntr + 1) % self.size


class TrueAfter:
    """
    Returns False if called <= after times
    Returns True otherwise
    """
    def __init__(self, after:int):
        self.after = after
        self.current = 0
        self.mybool = False

    def step(self):
        self.current += 1
        self.mybool = self.current > self.after

    def isafter(self):
        return self.mybool


class MovingAverageFilterPlus:
    
    """
    Track averages over iterations

    Includes cold start functionality that starts with buffer size 1 which increases until size
    """
    def __init__(self, cold_start:bool = False, initial_value:float = 0, size:int = 5):
        # Buffer size atleast 2 for trimmed average 
        self.size = max(size, 2)
        
        # Cold start condition
        # warm bool indicates if buffer has been filled
        if cold_start:
            self.warm = TrueAfter(self.size-1)
            init_val = 0
        else:
            self.warm = TrueAfter(0)
            init_val = initial_value

        self.buffer = [init_val] * self.size
        self.pntr = 0

    def iswarm(self):
        return self.warm

    def most_recent(self):
        return self.buffer[self.pntr - 1]

    def average(self):
        # Regular old average
        if self.warm.isafter():
            return sum(self.buffer) / self.size
        else:
            return sum(self.buffer) / max(self.pntr, 1)
        
    def trimmed_average(self):
        # Returns average without largest value in buffer
        if self.warm.isafter():
            return (sum(self.buffer) - max(self.buffer)) / (self.size - 1)
        elif self.pntr < 2:
            # Need atleast 2 element for trimmed average
            return sum(self.buffer)
        else:
            return (sum(self.buffer) - max(self.buffer)) / max(self.pntr - 1, 1)
    
    def update(self, val):
        self.size = min(self.size + 1, self.size)
        self.buffer[self.pntr] = val
        self.pntr = (self.pntr + 1) % self.size

        # Step TrueAfter
        self.warm.step()

class PID:
    """
    Generic DT PID controller
    """
    def __init__(self, Kp, Kd, Ki):
        self.Kp = Kp
        self.Kd = Kd
        self.Ki = Ki

        self.last_error = 0
        self.integral = 0
    
    def update(self, setpoint, measured, dt):
        error = setpoint - measured
        derivative = (error-self.last_error) / dt
        self.integral += error * dt

        output = self.Kp * error + self.Kd * derivative + self.Ki * self.integral
        self.last_error = error

        return output
