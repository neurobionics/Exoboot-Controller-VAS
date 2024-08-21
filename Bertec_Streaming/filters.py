import numpy as np
import time

class LowPassFilter:
    def __init__(self, w):
        self.w = w # Hz
        self.w_rad = 2 * np.pi * self.w

        self.state_time_prev = time.time()

        # Fill up history before filtering
        self.cold = True

    def update(self, x, state_time):
        if self.cold:
            self.x_prev = x
            self.y_prev = x
            self.state_time_prev = state_time

            self.cold = False
            return x
        
        # Filter Parameters
        dt = state_time - self.state_time_prev
        a = -(self.w_rad * dt - 2) / (self.w_rad * dt + 2)
        b = (self.w_rad * dt) / (self.w_rad * dt + 2)

        # Difference Equation
        y = a * self.y_prev + b * (x + self.x_prev)

        # Post updates
        self.y_prev = y
        self.x_prev = x
        self.state_time_prev = state_time

        return y