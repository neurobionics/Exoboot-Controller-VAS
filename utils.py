class MovingAverageFilter:
    # Use to track averages of some numerical quantity
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
    # Returns false if called <= after times
    # Returns true otherwise
    def __init__(self, after:int):
        self.after = after
        self.current = 0
        self.mybool = False

    def isafter(self):
        if self.mybool:
            return True
        else:
            self.current += 1
            self.mybool = self.current > self.after
            return self.mybool


class MovingAverageFilterPlus:
    # Use to track averages of max_size number of values
    # Plus adds cold start option fills buffer overtime until reaches max_size
    def __init__(self, cold_start:bool = False, initial_value:float = 0, size:int = 5):
        # Buffer size atleast 2 for trimmed average 
        self.size = max(size, 2)
        
        # Cold start condition
        # warm bool indicates if buffer has been filled
        if cold_start:
            self.warm = TrueAfter(self.size)
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
        elif self.pntr < 1:
            # Need atleast 2 element for trimmed average
            return sum(self.buffer)
        else:
            return (sum(self.buffer) - max(self.buffer)) / max(self.pntr - 1, 1)
    
    def update(self, val):
        self.size = min(self.size + 1, self.size)
        self.buffer[self.pntr] = val
        self.pntr = (self.pntr + 1) % self.size
