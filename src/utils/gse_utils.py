import time, sys, csv
import numpy as np

class WalkingSimulator():
    """
    Simulate a person walking with a fixed stride period.
    Increments current_time_in_stride at each update, until it resets at the stride period.
    Output looks like a sawtooth wave. 
    Ankle angle trajectory is from Reznick et al. 2021 (10° uphill walking)
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
            print(f'{self.stride_num} stride(s) completed')
        elif self.current_time_in_stride < self.stride_period:
            self.current_time_in_stride = time.time() - self.start_time
            print(f"time in curr stride: {self.current_time_in_stride:.3f}")
            
        return self.current_time_in_stride
    
    def update_ank_angle(self)-> float:
        """
        Updates the ankle angle based on the current time in stride.
        """
        percent_gc = self.time_in_stride_to_percent_GC(self.current_time_in_stride)
        
        # interpolate angle at the current % gait cycle
        interp_ang_at_query_pt = np.interp(percent_gc, self.gc, self.ank_ang)
        
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
        
        print(f"percent GC: {percent_GC:.2f}")
            
        return percent_GC
    
    # TODO: add a swing/stance differentiator
    
        