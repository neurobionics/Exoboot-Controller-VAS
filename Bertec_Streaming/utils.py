# miscellaneous Things

import csv
import numpy as np

class CircularBuffer:
    # Use to track averages of some numerical quantity
    def __init__(self, channels: int = 1, size:int = 100):
        self.size = size
        self.channels = channels
        self.buffer = np.zeros((self.channels, self.size))
        self.pntr = 0

    def mean(self):
        """Moving average filter of the data. Window size equivalent to buffer size."""
        return np.mean(self.buffer, axis=1)
    
    def update(self, *vargin):
        for i, val in enumerate(vargin):
            self.buffer[i, self.pntr] = val
        self.pntr = (self.pntr + 1) % self.size