import time, sys, csv
import numpy as np
from opensourceleg.utilities import SoftRealtimeLoop

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
    Simulate a person walking with a fixed stride period.
    Increments current_time_in_stride at each update, until it resets at the stride period.
    Output looks like a sawtooth wave. 
    """
    def __init__(self, stride_period:float=1.20):
        self.current_time_in_stride = 0
        self.stride_num = 0
        self.stride_period = stride_period
        self.start_time = time.time()
        
        # ankle angle trajectory from Reznick et al. 2021 (10° uphill walking)
        self.gc = [] 
        self.ank_ang = [] 
         
        try:
            with open('./src/utils/ankle_angle_trajectory.csv', 'r') as f:
                reader = csv.reader(f)
                
                for row in reader:
                    # skip the header
                    if row[0] == 1:
                        continue
                    else:
                        self.gc.append(float(row[0]))
                        self.ank_ang.append(float(row[1])) 
                    
        except Exception as err:
            print(f"Error when loading & parsing 'ankle_angle_trajectory.csv': {err}")
            print(err)
            sys.exit(1)
            
    def update_time_in_stride(self)-> float:
        """
        Updates the gait state based on the current time in stride.
        """
        if self.current_time_in_stride >= self.stride_period:
            self.current_time_in_stride = 0
            self.start_time = time.time()
            self.stride_num += 1
            # print(f'{self.stride_num} stride(s) completed')
        elif self.current_time_in_stride < self.stride_period:
            self.current_time_in_stride = time.time() - self.start_time
            # print(f"time in curr stride: {self.current_time_in_stride:.3f}")
            
        return self.current_time_in_stride
    
    def update_ank_angle(self)-> float:
        """
        Updates the ankle angle based on the current time in stride.
        """
        self.percent_gc = self.time_in_stride_to_percent_GC(self.current_time_in_stride)
        
        # interpolate angle at the current % gait cycle
        interp_ang_at_query_pt = np.interp(self.percent_gc, self.gc, self.ank_ang)
        
        return interp_ang_at_query_pt
        
    def time_in_stride_to_percent_GC(self, time_in_stride:float)-> float:
        """
        Converts the time in stride to a percentage of the gait cycle.
        """
        if time_in_stride < 0:
            raise ValueError("Time in stride cannot be negative.")
        elif time_in_stride > self.stride_period:
            percent_GC = 100
        else:
            percent_GC = time_in_stride / self.stride_period * 100
        
        # print(f"percent GC: {percent_GC:.2f}")
            
        return percent_GC
        

if __name__ == "__main__":
    sim = WalkingSimulator(stride_period=1.20)
    clock = SoftRealtimeLoop(dt=1 / 100)  # 1 Hz update rate
    print("Starting walking simulation. Press Ctrl+C to stop.")

    for _t in clock:
        try:
            time_in_stride = sim.update_time_in_stride()
            ank_angle = sim.update_ank_angle()
            print(f"Stride: {sim.stride_num}, Time in stride: {time_in_stride:.3f}s, Ankle angle: {ank_angle:.2f} deg")
        except KeyboardInterrupt:
            print("\nSimulation stopped by user.")
            sys.exit(0)