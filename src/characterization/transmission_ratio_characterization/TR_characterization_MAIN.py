import os, sys, csv, time, datetime, threading

import numpy as np
from time import sleep

from flexsea.device import Device

# from SoftRTloop import FlexibleSleeper

sys.path.insert(0, '/home/pi/VAS_exoboot_controller/')

from src.settings.constants import *

TR_FILE_PREFIX = "default_TR"
TR_COEFS_PREFIX = "{}_coefs".format(TR_FILE_PREFIX)
TR_FULLDATA_PREFIX = "{}_fulldata".format(TR_FILE_PREFIX)
TR_DATE_FORMATTER = "%Y_%m_%d_%H_%M"
BIAS_CURRENT = 500

class FlexibleSleeper():
    """
    Inactive timer using sleep by delay
    """
    def __init__(self, period):
        self.period = period
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

def get_active_ports():
    """
    To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo
    """
    try:
        device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)
        device_1.open()
        side_1 = DEV_ID_TO_SIDE_DICT[device_1.id]
        print("Device 1: {}, {}".format(device_1.id, side_1))
    except:
        side_1 = None
        device_1 = None
        print("DEVICE 1 NOT FOUND")

    try:
        device_2 = Device(port="/dev/ttyACM1", firmwareVersion="7.2.0", baudRate=230400, logLevel=3)
        device_2.open()
        side_2 = DEV_ID_TO_SIDE_DICT[device_2.id]
        print("Device 2: {}, {}".format(device_2.id, side_2))
    except:
        side_2 = None
        device_2 = None
        print("DEVICE 2 NOT FOUND")

    if not (device_1 or device_2):
        print("\nNO DEVICES: CONNECT AND POWER ON ATLEAST 1 EXOBOOT\n")
        quit()

    # Always assign first pair of outputs to left side
    if side_1 == "left" or side_2 == "right":
        return side_1, device_1, side_2, device_2
    elif side_1 == "right" or side_2 == "left":
        return side_2, device_2, side_1, device_1
    else:
        raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")

class TR_Characterizer:
    """
    Characterize Tranmission ratio of given exoboot
    """
    def __init__(self, side, flexdevice, current_cmd=BIAS_CURRENT, freq=500, fulldata_prefix=TR_FULLDATA_PREFIX, coefs_prefix=TR_COEFS_PREFIX, date=None):
        self.side = side
        self.flexdevice = flexdevice
        self.current_cmd = current_cmd
        
        # collect speeds
        self.freq = freq
        self.printfreq = freq/10

        # Get motor/ankle encoder signs
        self.motor_sign = DEV_ID_TO_MOTOR_SIGN_DICT[self.flexdevice.id]
        self.ank_enc_sign = DEV_ID_TO_ANK_ENC_SIGN_DICT[self.flexdevice.id]

        # Set filenames
        self.date = date if date else datetime.datetime.today().strftime(TR_DATE_FORMATTER)
        self.fulldata_filename = "{}_{}_{}.csv".format(fulldata_prefix, self.side, self.date)
        self.coefs_filename = "{}_{}_{}.csv".format(coefs_prefix, self.side, self.date)

        # Threading
        self.thread = None
        self.kill = False

    def collect(self):
        """
        This function collects a curve of motor angle vs. ankle angle which is differentiated
        later to get a transmission ratio curve vs. ankle angle. The ankle joint should be moved through
        the full range of motion (starting at extreme dorsiflexion to extreme plantarflexion on repeat)
        while this is running.
        """
        print("Starting ankle transmission ratio procedure...\n")
        
        # Conduct transmission ratio curve characterization procedure and store curve
        self.motorAngleVec = np.array([])
        self.ankleAngleVec = np.array([])
        
        iterations = 0
        with open(self.fulldata_filename, "w", newline="\n") as f:
            writer = csv.writer(f)
            self.flexdevice.command_motor_current(self.motor_sign * self.current_cmd)

            loopsleeper = FlexibleSleeper(period=1/self.freq)
            lastprint = time.perf_counter()
            while not self.kill:
                try:
                    all_data = self.flexdevice.read(allData=True)
                    act_pack = all_data[-1] # Newest data

                    iterations += 1

                    # Ankle direction convention:   plantarflexion: increasing angle, dorsiflexion: decreasing angle
                    current_ank_angle = (self.ank_enc_sign * act_pack['ank_ang'] * ENC_CLICKS_TO_DEG) - self.offset # deg
                    current_mot_angle = self.motor_sign * act_pack['mot_ang'] * ENC_CLICKS_TO_DEG # deg

                    act_current = act_pack['mot_cur']

                    self.motorAngleVec = np.append(self.motorAngleVec, current_mot_angle)
                    self.ankleAngleVec = np.append(self.ankleAngleVec, current_ank_angle)

                    # Print slower than loop freq
                    current_time = time.perf_counter()
                    if current_time - lastprint > 1/self.printfreq:
                        print("Begin rotating the angle joint starting from extreme dorsiflexion to extreme plantarflexion...\n")
                        print("Motor Angle: {} deg".format(current_mot_angle))
                        print("Ankle Angle: {} deg".format(current_ank_angle))
                        print("\nPress any key to stop characterization")
                        lastprint = current_time

                    writer.writerow([iterations, self.current_cmd, act_current, current_mot_angle, current_ank_angle])

                    loopsleeper.pause()
                except:
                    pass

        # fit a 3rd order polynomial to the ankle and motor angles
        self.motor_angle_curve_coeffs = np.polyfit(self.ankleAngleVec, self.motorAngleVec, 3)
        
        # polynomial deriv coefficients (derivative of the motor angle vs ankle angle curve yields the TR)
        self.TR_curve_coeffs = np.polyder(self.motor_angle_curve_coeffs)

        print("Char curve")
        print(str(self.motor_angle_curve_coeffs))
        print("TR curve")
        print(str(self.TR_curve_coeffs))
        print(self.offset)
        
        print("Exiting curve characterization procedure")
        self.flexdevice.command_motor_current(0)
        sleep(0.5)
        
        with open(self.coefs_filename, "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(self.motor_angle_curve_coeffs)
            writer.writerow(self.TR_curve_coeffs)
            writer.writerow([self.offset])

        print("Collect Finished\n")
        
    def start(self):
        self.flexdevice.command_motor_current(self.motor_sign * self.current_cmd)
        
        input("Set ankle angle to maximum dorsiflexion hardstop. Press any key to lock in angle/offset at this ankle position")
        act_pack = self.flexdevice.read()
        self.offset = self.ank_enc_sign * act_pack['ank_ang'] * ENC_CLICKS_TO_DEG
        print("OFFSET: ", self.offset)

        input("Press any key to continue")
        self.thread = threading.Thread(target=self.collect, args=())
        self.thread.start()

    def stop(self):
        self.kill = True
        self.thread.join()


if __name__ == "__main__":
    # Get active ports
    side_left, device_left, side_right, device_right = get_active_ports()

    devices = [device_left, device_right]
    sides = [side_left, side_right]
    
    # Get YEAR_MONTH_DAY_HOUR_MINUTE
    date = datetime.datetime.today().strftime(TR_DATE_FORMATTER)

    # Start device streaming and set gains:
    print("Starting TR Characterization")
    frequency = 1000
    for side, device in zip(sides, devices):
        if device:
            device.start_streaming(frequency)
            device.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)

            characterizer = TR_Characterizer(side, device, BIAS_CURRENT, date=date)
            
            print("Starting {} Characterization".format(side.upper()))
            characterizer.start()
            input() #"Press any key to stop TR characterization of exoboot"
            characterizer.stop()

    # Stop motors
    for device in devices:
        if device:
            device.stop_motor()

    print("TR Characterization finished. Goodbye")

