import sys 
sys.path.append(r"C:/Users/nundinir/Downloads/SoftRTloop/")

from Vicon import ViconSDK_Wrapper
from ZMQ_PubSub import Publisher 
import time
from SoftRTloop import FlexibleTimer
from utils import CircularBuffer
from filters import LowPassFilter

vicon = ViconSDK_Wrapper('localhost','801') 
bertec_period_tracker = CircularBuffer(channels=2, size=500)

# Get force data from bertec 
pub = Publisher()
loopFreq = 1000 # Hz

filter_w = 5.0  # Hz
left_fp_filter = LowPassFilter(filter_w)
right_fp_filter = LowPassFilter(filter_w)
# softRTloop = FlexibleTimer(target_freq=loopFreq)	# instantiate soft real-time loop

starting_time = time.time()
prev_time = starting_time
count = 0
print_every = 2000
try:
    while True:
        collection_time = time.time()
        z_forces = [f*-1 for f in vicon.get_latest_device_values(["RightForcePlate", "LeftForcePlate"], ["Force"], ["Fz"])] #this is done on the Vicon computer 

        z_filt_right = right_fp_filter.update(z_forces[0], collection_time)
        z_filt_left = left_fp_filter.update(z_forces[1], collection_time)

        # pub.send_array(z_forces)
        pub.publish('time', '%f' %collection_time)
        pub.publish('fz_right','% f' %z_filt_right)
        pub.publish('fz_left', '%f' %z_filt_left)

        # Clock the Frequency of the loop
        end_time = time.time()
        bertec_period_tracker.update(end_time-prev_time, vicon.get_streaming_latency())
        prev_time = end_time

        count += 1
        if count > print_every:
            [period, latency] = bertec_period_tracker.mean()
            print("Time alive: {:.2f} seconds".format(prev_time - starting_time))
            print("Streaming Latency: {}".format(latency))
            print("Loop Frequency:", 1/period)
            # print("Raw FP Data:", z_forces)
            # print("Filtered FP Data:", [z_filt_right, z_filt_left])
            print()
            count = 0
            
except KeyboardInterrupt:
    print("Stopping Streaming")