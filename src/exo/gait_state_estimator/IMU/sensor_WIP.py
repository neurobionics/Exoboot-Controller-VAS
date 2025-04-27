import numpy as np
import threading
import time
from typing import Type
from collections import deque

from constants import *
from filters import LowPassFilter

from src.utils.utils import MovingAverageFilter

class Sensor(threading.Thread):
    def __init__(self, fxs, devices: list, name:str='sensor', quit_event=Type[threading.Event]):
        # TODO implement in full
        super().__init__(name=name)
        self.devices = devices
        self.quit_event = quit_event

        # Keys: FlexSEA device channels
        # Values: Functions which evaluated during collect
        # Function signature: (raw_data, device, state_time)
        self.channels_dict = {
                'state_time':   lambda state_time, *_: state_time / 1000,
                'temperature':  lambda temperature, *_: temperature,
                # 'ank_ang':      lambda ank_ang, device, *_: device.correct_ankle_angle(ank_ang),
                'ank_ang':      lambda ank_ang, *_: ank_ang,
                'ank_vel':      lambda ank_vel, *_: ank_vel / 10,
                # 'mot_ang':      lambda mot_ang, device, *_: device.correct_motor_angle(mot_ang),
                'mot_ang':      lambda mot_ang, *_: mot_ang,
                'mot_vel':      lambda mot_vel, *_: mot_vel,
                'accelx':       lambda accelx, *_: ACCELX_SIGN * accelx * ACCEL_GAIN,
                'accely':       lambda accely, *_: ACCELY_SIGN * accely * ACCEL_GAIN,
                'accelz':       lambda accelz, *_: ACCELZ_SIGN * accelz * ACCEL_GAIN,
                'gyrox':        lambda gyrox, *_: GYROX_SIGN * gyrox * GYRO_GAIN,
                'gyroy':        lambda gyroy, *_: GYROY_SIGN * gyroy * GYRO_GAIN,
                'gyroz':        LowPassFilter(GYROZ_W0, lambda gyroz: GYROZ_SIGN * gyroz * GYRO_GAIN).update,
                }

        self.num_devices = len(devices)
        self.num_channels = len(self.channels_dict)

        # Data storage buffer
        self.sensor_buffers_dict = {device: deque() for i, device in enumerate(devices)}

    def sensor_buffer_append(self, device, data_as_array):
        self.sensor_buffers_dict[device].append(data_as_array)

    def sensor_buffer_flush(self, device):
        # Get data in buffer
        buffer_contents = list(self.sensor_buffers_dict[device])

        # Clear buffer
        self.sensor_buffers_dict[device].clear()
        return buffer_contents

    def collect(self):
        # For each device, read sensor data into buffer
        # Uses functions/filter methods from channels_dict
        for device in self.devices:
            # side = DEV_ID_TO_SIDE_DICT[device]

            data = device.read(allData=True)

            state_time = data.state_time / 1000

            data_as_array = np.zeros(self.num_channels)
            for i, field in enumerate(self.channels_dict.keys()):
                raw_ = getattr(data, field)
                val_ = self.channels_dict[field](raw_, device, state_time)
                data_as_array[i] = val_

            # Update sensor buffer
            self.sensor_buffer_append(device, data_as_array)

    def run(self):
        # Track sensor average period
        self.period_tracker = MovingAverageFilter(initial_value=0, size=500)

        prev_time = time.time()
        while self.quit_event.is_set():
            self.collect()

            # Update period_tracker
            end_time = time.time()
            self.period_tracker.update(end_time - prev_time)
            prev_time = end_time
