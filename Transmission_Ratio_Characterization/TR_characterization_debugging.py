# TESTING ONLY
# modify TR_curve_calibration method in ExoClass.py
# remove the motor angle and ankle angle offset when computing TR
# call on plot_TR_motor_angle_curves method to plot the TR and motor-angle curves

import csv
import threading
import numpy as np

from scipy import interpolate
from scipy import signal
from time import time, sleep

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

from ExoClass import ExoObject
import config

def get_active_ports(fxs):
    """To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo.
    """

    port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
    ports, baud_rate = fxu.load_ports_from_file(port_cfg_path) #Flexsea api initialization

    # Always turn left exo on first for ports to line up or switch these numbers
    print("active ports recieved")

    dev_id_1 = fxs.open(ports[0], config.BAUD_RATE, 6)
    dev_id_2 = fxs.open(ports[1], config.BAUD_RATE, 6)

    print("dev_id_1",dev_id_1)
    print("dev_id_2",dev_id_2)

    if(dev_id_1 in config.LEFT_EXO_DEV_IDS):
        side_1  = 'left'
        side_2 = 'right'
    elif(dev_id_1 in config.RIGHT_EXO_DEV_IDS):
        side_1 = 'right' 
        side_2 = 'left'

    return side_1, dev_id_1, side_2, dev_id_2

class TR_Characterizer:
    def __init__(self, exo):
        self.exo = exo
        self.full_filename = "TR_full_raw_enc_data_{}.csv".format(self.exo.side)
        self.coefs_filename = "TR_fitted_data_{}.csv".format(self.exo.side)

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
        self.motorClicksVec = np.array([])
        self.ankleClicksVec = np.array([])
        startTime = time()

        pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet
        desCurrent = pullCurrent * self.exo.exo_left_or_right_sideMultiplier
        
        iterations = 0
        with open(self.full_filename, "w", newline="\n") as fd:
            writer = csv.writer(fd)
            self.exo.fxs.send_motor_command(self.exo.dev_id, fxe.FX_CURRENT, desCurrent)
            while not self.kill:
                act_pack = self.exo.fxs.read_device(self.exo.dev_id)
                fxu.clear_terminal()
                iterations += 1

                # Ankle Angle convention (extreme plantar: decreasing angle (0), extreme dorsi: increasing angle (180))                
                current_ank_angle = act_pack.ank_ang * config.ENC_CLICKS_TO_DEG    # obtain ankle angle in deg
                current_mot_angle = act_pack.mot_ang * config.ENC_CLICKS_TO_DEG    # obtain motor angle in deg

                act_current = act_pack.mot_cur
                currentTime = time()

                self.motorAngleVec = np.append(self.motorClicksVec, current_mot_angle)
                self.ankleAngleVec = np.append(self.ankleClicksVec, current_ank_angle)

                print("Begin rotating the angle joint starting from extreme dorsiflexion to extreme plantarflexion...\n")
                print("Motor Angle: {} deg".format(current_mot_angle))
                print("Ankle Angle: {} deg".format(current_ank_angle))
                print("\nPress any key to stop characterization")
                sleep(1/250)
                if iterations == 1:
                    writer.writerow(['iters', 'setpt_current', 'applied_current', 'motor_ang', 'ank_ang'])
                else:
                    writer.writerow([iterations, desCurrent, act_current, current_mot_angle, current_ank_angle])

        
        motor_angles = np.array(self.motorAngleVec) 
        ankle_angles = np.array(self.ankleAngleVec)
        
        # Sort the data points
        zipped_sorted_lists = sorted(zip(ankle_angles, motor_angles))
        mytuples = zip(*zipped_sorted_lists)
        ankle_angles, motor_angles = [list(mytuple) for mytuple in mytuples]
        
        # Filter
        b, a = signal.butter(N=1, Wn=0.05)
        motor_angles = signal.filtfilt(b, a, motor_angles, method="gust")
        ankle_angles = signal.filtfilt(b, a, ankle_angles, method="gust")
        
        # -1 multiplier since plantarflexion angle < dorsiflexion angles for right exo (dephy convention)
        # 180° at max dorsi, roughly 90° for vertical, 0° for max plantar
        relative_ankle_angles = (self.offset - ankle_angles) # from 0 = dorsi, goes onto plantar
        # relative_ankle_angles = -1*(ankle_angles = self.offset)
        print('Rel Standing Angle:', (self.offset - self.approx_standing_ang))  # angle at which plantarflexion begins from standing angle
        # print('Rel Standing Angle:', -1*(self.approx_standing_ang - self.offset))  # angle at which plantarflexion begins from standing angle
        
        # fit a 5th order polynomial to the ankle and motor angles
        self.motor_angle_curve_coeffs = np.polyfit(relative_ankle_angles, motor_angles, 5)
        print('Polynomial coefficients: ', self.motor_angle_curve_coeffs)
        polyfitted_motor_angle = np.polyval(self.motor_angle_curve_coeffs, relative_ankle_angles)

        # polynomial deriv coefficients (derivative of the motor angle vs ankle angle curve yields the TR)
        self.TR_curve_coeffs = np.polyder(self.motor_angle_curve_coeffs)
        print('Polynomial deriv coefficients: ', self.TR_curve_coeffs)
        TR_from_polyfit = np.polyval(self.TR_curve_coeffs, relative_ankle_angles)
        
        #####################################################
        ##### For Debugging: relative to standing angle #####
        rel_ank_ang_stand_ang = (ankle_angles - self.approx_standing_ang) # -ve = plantar, +ve = dorsi
        motor_angle_coeffs_standing = np.polyfit(rel_ank_ang_stand_ang, motor_angles, 5)
        polyfitted_motor_angle_rel_stand = np.polyval(motor_angle_coeffs_standing, rel_ank_ang_stand_ang)
        TR_curve_coeffs_standing = np.polyder(motor_angle_coeffs_standing)
        TR_from_polyfit_standing = np.polyval(TR_curve_coeffs_standing, rel_ank_ang_stand_ang)
        #####################################################
        
        # TODO (nundini): find the x-intercept and cut ann relative angles and 
        # TR's prior to that x-intercept since we can only actuate to provide plantarflexion assistance
        
        print("Exiting curve characterization procedure")
        self.exo.fxs.send_motor_command(self.exo.dev_id, fxe.FX_CURRENT, 0)
        sleep(0.5)
        
        # Stack the arrays into columns
        reshaped_rel_ankle_angles = np.reshape(np.array(relative_ankle_angles), (len(relative_ankle_angles), 1))
        reshaped_motor_angles = np.reshape(np.array(motor_angles), (len(relative_ankle_angles), 1))
        reshaped_polyfitted_motor_angle = np.reshape(np.array(polyfitted_motor_angle), (len(relative_ankle_angles), 1))
        reshaped_TR_from_polyfit = np.reshape(np.array(TR_from_polyfit), (len(relative_ankle_angles), 1))
       
       # reshaping rel standing angles:
        reshaped_rel_ank_ang_stand_ang = np.reshape(np.array(rel_ank_ang_stand_ang), (len(rel_ank_ang_stand_ang), 1))
        reshaped_polyfitted_motor_angle_rel_stand = np.reshape(np.array(polyfitted_motor_angle_rel_stand), (len(rel_ank_ang_stand_ang), 1))
        reshaped_TR_from_polyfit_standing = np.reshape(np.array(TR_from_polyfit_standing), (len(rel_ank_ang_stand_ang), 1))
       
        data = np.column_stack((reshaped_rel_ankle_angles, reshaped_motor_angles, reshaped_polyfitted_motor_angle,reshaped_TR_from_polyfit,
                                reshaped_rel_ank_ang_stand_ang, reshaped_polyfitted_motor_angle_rel_stand, reshaped_TR_from_polyfit_standing))
    
        # Write the data to a CSV file
        with open(self.coefs_filename, "w") as file:
            writer = csv.writer(file, delimiter= ",")
            writer.writerow(['rel_ank_angles', 'motor_angles', 'polyfitted_motor_angle', 'TR_from_polyfit',
                             'rel_stand_ank_ang', 'polyfitted_rel_stand_ang','TR_stand_ang'])
            writer.writerows(data)

        print("Collect Finished\n")
        
    def start(self):
        pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet
        desCurrent = pullCurrent * self.exo.exo_left_or_right_sideMultiplier
        self.exo.fxs.send_motor_command(self.exo.dev_id, fxe.FX_CURRENT, desCurrent)
        
        input("Set ankle angle to maximum dorsiflexion hardstop. Press any key to lock in angle/offset at this ankle position")
        act_pack = self.exo.fxs.read_device(self.exo.dev_id)
        self.offset = act_pack.ank_ang * self.exo.ANK_ENC_CLICKS_TO_DEG
        print(self.offset)
        
        input("Set ankle angle to approximate standing angle. Press any key to lock in angle/offset at this ankle position")
        act_pack = self.exo.fxs.read_device(self.exo.dev_id)
        self.approx_standing_ang = act_pack.ank_ang * self.exo.ANK_ENC_CLICKS_TO_DEG
        print(self.approx_standing_ang)

        input("Press any key to continue")
        self.thread = threading.Thread(target=self.collect, args=())
        self.thread.start()

    def stop(self):
        self.kill = True
        self.thread.join()


if __name__ == "__main__":
    # Recieve active ports that the exoskeletons are connected to
    fxs = flex.FlexSEA()
    side_1, dev_id_1, side_2, dev_id_2 = get_active_ports(fxs)
    sleep(0.5)

    # Instantiate exo object for both left and right sides
    if(side_1 == 'left'):
        exoLeft = ExoObject(fxs,side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=6)
        exoRight = ExoObject(fxs,side=side_2, dev_id = dev_id_2,stream_freq=1000, data_log=False, debug_logging_level=6)
    else:
        exoLeft = ExoObject(fxs,side=side_2, dev_id = dev_id_2, stream_freq=1000, data_log=False, debug_logging_level=6)
        exoRight = ExoObject(fxs,side=side_1, dev_id = dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=6)

    sleep(0.5)
    # Start streaming
    exoLeft.start_streaming()
    exoRight.start_streaming()
    sleep(0.5)
    
    # Collect the transmission ratio & motor-angle coefficients anytime the belts are replaced
    print("Starting TR Characterization")

    char_Right = TR_Characterizer(exoRight)
    char_Right.start()
    input() #"Press any key to start TR characterization of RIGHT exo"
    char_Right.stop()
    print("TR Characterization successful. Goodbye")

    