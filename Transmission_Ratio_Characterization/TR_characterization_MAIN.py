# MAIN SCRIPT TO PERFORM TR CHARACTERIZATION 

import csv
import threading
import numpy as np
from time import time, sleep
from flexsea.device import Device
import sys
sys.path.insert(0, '/home/pi/Exoboot-Controller-VAS/')
from ExoClass import ExoObject
import config

def get_active_ports():
    """To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo.
     """
    print("in get_active_ports")
    device_1 = Device(port="/dev/ttyACM0", firmwareVersion="7.2.0", baudRate=230400, logLevel=6)
    device_2 = Device(port="/dev/ttyACM1", firmwareVersion="7.2.0", baudRate=230400, logLevel=6)
    
    # Establish a connection between the computer and the device    
    device_1.open()
    device_2.open()
    
    print("Dev1", device_1.id, device_1.connected)
    print("Dev2", device_2.id, device_2.connected)
    print("opened comm with device")
    
    if(device_1.id in config.LEFT_EXO_DEV_IDS):
        side_1  = 'left'
        side_2 = 'right'
    elif(device_1.id in config.RIGHT_EXO_DEV_IDS):
        side_1 = 'right' 
        side_2 = 'left'
    
    print("device connected and active ports recieved")

    return side_1, device_1, side_2, device_2

class TR_Characterizer:
    def __init__(self, exo):
        self.exo = exo
        self.full_filename = "Transmission_Ratio_Characterization/default_TR_fulldata_{}.csv".format(self.exo.side)
        self.coefs_filename = "Transmission_Ratio_Characterization/default_TR_coefs_{}.csv".format(self.exo.side)

        self.thread = None
        self.kill = False

    def collect(self):
        """This function collects a curve of motor angle vs. ankle angle which is differentiated
        later to get a transmission ratio curve vs. ankle angle. The ankle joint should be moved through
        the full range of motion (starting at extreme dorsiflexion to extreme plantarflexion on repeat)
        while this is running.
        """

        print("Starting ankle transmission ratio procedure...\n")
        
        # conduct transmission ratio curve characterization procedure and store curve
        self.motorAngleVec = np.array([])
        self.ankleAngleVec = np.array([])
        startTime = time()

        pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet
        desCurrent = pullCurrent * self.exo.exo_left_or_right_sideMultiplier
        
        iterations = 0
        with open(self.full_filename, "w", newline="\n") as fd:
            writer = csv.writer(fd)
            self.exo.device.command_motor_current(desCurrent)
            
            while not self.kill:
                act_pack = self.exo.device.read()
                # fxu.clear_terminal()
                iterations += 1

                # Ankle direction convention:   plantarflexion: increasing angle, dorsiflexion: decreasing angle
                current_ank_angle = (self.exo.ank_enc_sign * act_pack['ank_ang'] * self.exo.ANK_ENC_CLICKS_TO_DEG) - self.offset # deg
                current_mot_angle = self.exo.exo_left_or_right_sideMultiplier * act_pack['mot_ang'] * self.exo.ANK_ENC_CLICKS_TO_DEG # deg

                act_current = act_pack['mot_cur']
                currentTime = time()

                self.motorAngleVec = np.append(self.motorAngleVec, current_mot_angle)
                self.ankleAngleVec = np.append(self.ankleAngleVec, current_ank_angle)

                print("Begin rotating the angle joint starting from extreme dorsiflexion to extreme plantarflexion...\n")
                print("Motor Angle: {} deg".format(current_mot_angle))
                print("Ankle Angle: {} deg".format(current_ank_angle))
                print("\nPress any key to stop characterization")
                sleep(1/250)

                writer.writerow([iterations, desCurrent, act_current, current_mot_angle, current_ank_angle])

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
        self.exo.device.command_motor_current(0)
        sleep(0.5)
        
        with open(self.coefs_filename, "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(self.motor_angle_curve_coeffs)
            writer.writerow(self.TR_curve_coeffs)
            writer.writerow([self.offset])

        print("Collect Finished\n")
        
    def start(self):
        pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet
        desCurrent = pullCurrent * self.exo.exo_left_or_right_sideMultiplier
        self.exo.device.command_motor_current(desCurrent)

        # self.exo.fxs.send_motor_command(self.exo.dev_id, fxe.FX_CURRENT, desCurrent)
        
        input("Set ankle angle to maximum dorsiflexion hardstop. Press any key to lock in angle/offset at this ankle position")
        act_pack = self.exo.device.read()
        self.offset = self.exo.ank_enc_sign * act_pack['ank_ang'] * self.exo.ANK_ENC_CLICKS_TO_DEG 
        print(self.offset)

        input("Press any key to continue")
        self.thread = threading.Thread(target=self.collect, args=())
        self.thread.start()

    def stop(self):
        self.kill = True
        self.thread.join()


if __name__ == "__main__":
    # Recieve active ports that the exoskeletons are connected to
    # fxs = flex.FlexSEA()
    
    side_1, device_1, side_2, device_2 = get_active_ports()
    print(side_1, device_1.id, side_2, device_2.id)
    
    # start device streaming and set gains:
    frequency = 1000
    device_1.start_streaming(frequency)
    device_2.start_streaming(frequency)
    device_1.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)
    device_2.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)

    # Instantiate exo object for both left and right sides
    if(side_1 == 'left'):
        exo_left = ExoObject(side = side_1, device = device_1)
        exo_right = ExoObject(side = side_2, device = device_2)
    else:
        exo_left = ExoObject(side=side_2, device = device_2)
        exo_right = ExoObject(side=side_1, device = device_1)
    
    # Collect the transmission ratio & motor-angle coefficients anytime the belts are replaced
    print("Starting TR Characterization")
    char_Left = TR_Characterizer(exo_left)
    char_Left.start()
    input() #"Press any key to stop TR characterization of LEFT exo"
    char_Left.stop()

    char_Right = TR_Characterizer(exo_right)
    char_Right.start()
    input() #"Press any key to stop TR characterization of RIGHT exo"
    char_Right.stop()
    print("TR Characterization successful. Goodbye")
