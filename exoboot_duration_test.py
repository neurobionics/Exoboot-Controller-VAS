# Description:
# This script is the main controller for the VAS Vickrey Protocol.
# It is responsible for initializing the exoskeletons, calibrating them, and running the main control loop.
#
# Original template created by: Emily Bywater
# Modified for VAS Vickrey protocol by: Nundini Rawal, John Hutchinson
# Date: 06/13/2024

# TODO: downgrade library, rtplotting, gse_imu, fix bertec estimator, find delay, check thread frequencies

import os, sys, csv, time, socket, threading

from flexsea.device import Device
from rtplot import client

from validator import Validator
from ExoClass_thread import ExobootThread
from GaitStateEstimator_thread import GaitStateEstimator
from exoboot_remote_control import ExobootRemoteServerThread
from LoggingClass import LoggingNexus, FilingCabinet

from SoftRTloop import FlexibleSleeper
from constants import *
from flexsea.fx_enums import FX_CURRENT

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

def get_active_ports():
    """
    To use the exos, it is necessary to define the ports they are going to be connected to.
    These are defined in the ports.yaml file in the flexsea repo
    """
    # port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
    device_1 = Device(port="/dev/ttyACM0", baud_rate=BAUD_RATE)
    device_2 = Device(port="/dev/ttyACM1", baud_rate=BAUD_RATE)

    # Establish a connection between the computer and the device AND start streaming
    device_1.open(freq=STREAMING_FREQ, log_level=3, log_enabled=True)
    device_2.open(freq=STREAMING_FREQ, log_level=3, log_enabled=True)

    # Get side from side_dict
    side_1 = DEV_ID_TO_SIDE_DICT[device_1.dev_id]
    side_2 = DEV_ID_TO_SIDE_DICT[device_2.dev_id]

    print("Device 1: {}, {}".format(device_1.dev_id, side_1))
    print("Device 2: {}, {}".format(device_2.dev_id, side_2))

    # Always assign first pair of outputs to left side
    if side_1 == 'left':
        return side_1, device_1, side_2, device_2
    elif side_1 == 'right':
        return side_2, device_2, side_1, device_1
    else:
        raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")


if __name__ == "__main__":
    side_left, device_left, side_right, device_right = get_active_ports()

    # Start device streaming and set gains:
    device_left.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)
    device_right.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)

    use_device = device_left

    time.sleep(1.0)
    with open("exobootleft_dur_test.csv", "w") as file:
        writer = csv.writer(file, delimiter=",")

        # use_device.send_motor_command(FX_CURRENT, -1 * 750)

        for _ in range (200):
            data = use_device.read()

            data_list = []

            # Exoboot Time
            state_time = data.state_time / 1000 #converting to seconds

            # Accelerometer
            # Note based on the MPU reading script it says the accel = raw_accel/accel_sace * 9.80605 -- so if the value of accel returned is multiplyed  by the gravity term then the accel_scale for 4g is 8192
            accel_x = data.accelx * ACCEL_GAIN  #This is in the walking direction {i.e the rotational axis of the frontal plane}
            accel_y = -1 * data.accely * ACCEL_GAIN # This is in the vertical direction {i.e the rotational axis of the transverse plane}
            accel_z = data.accelz * ACCEL_GAIN # This is the rotational axis of the sagital plane
            motor_angle = data.mot_ang * ENC_CLICKS_TO_DEG
            motor_current = data.mot_cur
            gyro_x = -1 * data.gyrox * GYRO_GAIN
            gyro_y = data.gyroy * GYRO_GAIN
            gyro_z = data.gyroz * GYRO_GAIN



            writer.writerow([state_time, accel_x, accel_y, accel_z, motor_angle, motor_current, gyro_x, gyro_y, gyro_z])

            time.sleep(0.01)

        file.close()