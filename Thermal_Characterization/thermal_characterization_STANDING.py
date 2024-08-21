# Performing Thermal Testing to Answer the Following Questions:
# 
# 1). How long can we sustain 27A/peak instantaneous torque?
# 2). Can winding and casing temperatures remain below 100°C and 75°C, respectively 
# after 15 minutes of peak torque?
# 3). How well do the thermal model predictions match actual case temperature?
#
# General Testing Procedure: 
# Tester is standing while wearing the exo. The device will 
# actuate according to the four-point-spline algorithm and will be backdriven by the 
# user during "swing" phase for 10 minutes OR until the thermal/current shut-off engages.
# Case temperatures from Dephy will be recorded, as well as modeled case & winding 
# temperatures. Thermal camera (FLIR) data will also be collected to determine the 
# hottest parts of the driver board ontop of the motor.
#
# author: Nundini Rawal
# date: 7/4/24

import os
import csv
import traceback
import numpy as np
from time import time, sleep

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

import sys
sys.path.insert(0, '/home/pi/VAS_exoboot_controller/')
from ExoClass import ExoObject
from SoftRTloop import FlexibleTimer
import config

def get_active_ports(fxs):
    """To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo.
    """

    port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
    ports, baud_rate = fxu.load_ports_from_file(port_cfg_path) #Flexsea api initialization

    # Always turn left exo on first for ports to line up or switch these numbers
    print("active ports recieved")

    dev_id_1 = fxs.open(ports[0], config.BAUD_RATE, 3)
    dev_id_2 = fxs.open(ports[1], config.BAUD_RATE, 3)

    print("dev_id_1",dev_id_1)
    print("dev_id_2",dev_id_2)

    if(dev_id_1 in config.LEFT_EXO_DEV_IDS):
        side_1  = 'left'
        side_2 = 'right'
    elif(dev_id_1 in config.RIGHT_EXO_DEV_IDS):
        side_1 = 'right' 
        side_2 = 'left'

    return side_1, dev_id_1, side_2, dev_id_2
    

if __name__ == "__main__":
    # Recieve active ports that the exoskeletons are connected to
    fxs = flex.FlexSEA()
    side_1, dev_id_1, side_2, dev_id_2 = get_active_ports(fxs)

    # Instantiate exo object for both left and right sides
    if(side_1 == 'left'):
        exoLeft = ExoObject(fxs, side=side_1, dev_id=dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)
        exoRight = ExoObject(fxs, side=side_2, dev_id=dev_id_2, stream_freq=1000, data_log=False, debug_logging_level=3)
    else:
        exoLeft = ExoObject(fxs, side=side_2, dev_id=dev_id_2, stream_freq=1000, data_log=False, debug_logging_level=3)
        exoRight = ExoObject(fxs, side=side_1, dev_id=dev_id_1, stream_freq=1000, data_log=False, debug_logging_level=3)

    # Start streaming
    exoLeft.start_streaming()
    exoRight.start_streaming()
    
    input('Press ANY KEY to spool the RIGHT exo belt')
    
    exoLeft.spool_belt()
    
    input('Press ANY KEY to load in Transmission Ratio and FSM params')
    
    # loading in TR curve
    coefficients = exoLeft.load_TR_curve_coeffs()
    
    # load in the 4-point spline parameters:
    exoLeft.set_spline_timing_params(config.spline_timing_params)
    
    print('Thermal Testing for RIGHT Exo ONLY will commence shortly...')

    peak_current = input("Define a peak current amount (in mA): ")
    peak_current = float(peak_current)
    
    if(side_1 == 'left'):
        L_exo_filename = "/home/pi/VAS_exoboot_controller/Thermal_Characterization/thermal_fulldata_{}_{}mA.csv".format(side_1, peak_current)
        R_exo_filename = "/home/pi/VAS_exoboot_controller/Thermal_Characterizationthermal_fulldata_{}_{}mA.csv".format(side_2, peak_current)
    else:
        L_exo_filename = "/home/pi/VAS_exoboot_controller/Thermal_Characterizationthermal_fulldata_{}_{}mA.csv".format(side_2, peak_current)
        R_exo_filename = "/home/pi/VAS_exoboot_controller/Thermal_Characterizationthermal_fulldata_{}_{}mA.csv".format(side_1, peak_current)
    
    act_current = np.array([])
    act_T_c = np.array([])
    modelled_T_c = np.array([])
    modelled_T_w = np.array([])
    torques = np.array([])
    array_time_in_current_stride = np.array([])
    motor_currs = np.array([])
    
    input('Press ANY KEY if you are ready to begin thermal testing')
    
    inProcedure = True
    loopFreq = 60 # Hz
    softRTloop = FlexibleTimer(target_freq=loopFreq)	# instantiate soft real-time loop 
    
    # Iterate through your state machine controller that controls the exos 
    iterations = 0
    current_time_in_stride = 0
    stride = 0
    stride_period = 1.12
    exo_safety_shutoff_flag = False
    
    start_time = time()
    
    with open(R_exo_filename, "w", newline="\n") as fd:
        writer = csv.writer(fd)

        while inProcedure:
            iterations += 1
            # fxu.clear_terminal()
            os.system('clear')
            try:
                # soft real-time loop
                softRTloop.pause()

                # simulate a gait state estimator: set a fixed stride period of 2s & 
                # increase current_time_in_stride in increments of 0.01s. 
                if current_time_in_stride >= stride_period:
                    current_time_in_stride = 0
                    start_time = time()
                    stride += 1
                    print('{} stride(s) completed', stride)
                elif current_time_in_stride < stride_period:
                    current_time_in_stride = time() - start_time
                    print("time in curr stride: ", current_time_in_stride)

                # command the exoskeleton using 4-point spline: 
                # desired_spline_torque = exoRight.fourPtSpline.torque_generator_MAIN(current_time_in_stride, 
                                                                            # stride_period, commanded_torque)

                # read from the exoskeleton (testing without Varun's GSE/sensor reading thread)
                act_pack = exoLeft.fxs.read_device(exoLeft.dev_id)

                current_ank_angle = (exoLeft.ank_enc_sign*act_pack.ank_ang * exoLeft.ANK_ENC_CLICKS_TO_DEG) - exoLeft.max_dorsi_offset  # obtain ankle angle in deg wrt max dorsi offset
                current_mot_angle = (act_pack.mot_ang * exoLeft.MOT_ENC_CLICKS_TO_DEG)  # obtain motor angle in deg
                
                # Convert spline torque to it's corresponding current
                # N = exoLeft.get_TR_for_ank_ang(float(current_ank_angle),coefficients)
                # spline_current = (desired_spline_torque / (N * exoRight.efficiency * exoRight.Kt))* exoRight.exo_left_or_right_sideMultiplier   # mA

                spline_current = exoLeft.fourPtSpline.current_generator_test(current_time_in_stride, stride_period, peak_current)
                print("commanded current: ", spline_current)    # current in terms of mA

                # Check whether commanded current is above the maximum current threshold
                vetted_current = exoLeft.max_current_safety_checker(spline_current)

                # Current control if desired torque is greater than minimum holding torque, otherwise position control
                exoLeft.fxs.send_motor_command(exoLeft.dev_id, fxe.FX_CURRENT, vetted_current)
                    
                # determine actual case temperature & motor current
                actpack_current = act_pack.mot_cur
                act_T_case = act_pack.temperature
                act_V = act_pack.mot_volt
                print("measured case temp: ", act_T_case)
                print("actpack_current", actpack_current)

                # determine modeled case & winding temp
                exoLeft.thermalModel.T_c = act_T_case
                exoLeft.thermalModel.update(dt=(1 / loopFreq), motor_current=actpack_current)
                exoLeft.winding_temperature = exoLeft.thermalModel.T_w

                # Shut off exo if thermal limits breached
                if act_T_case >= exoLeft.max_case_temperature:
                    exo_safety_shutoff_flag = True 
                    print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
                if exoLeft.winding_temperature >= exoLeft.max_winding_temperature:
                    exo_safety_shutoff_flag = True 
                    print("Winding Temperature has exceed 115°C soft limit. Exiting Gracefully")

                # Shut off the exo motors and exit out of loop gracefully
                if exo_safety_shutoff_flag == True:
                    print("Exiting curve characterization procedure")
                    exoLeft.fxs.send_motor_command(exoLeft.dev_id, fxe.FX_CURRENT, 0)
                    sleep(0.5)
                    # exit out of method and while loop
                    """Exit the execution loop"""
                    inProcedure = False

                # write data to csv
                # writer.writerow([current_time_in_stride, vetted_current, act_T_case, exoRight.thermalModel.T_c, exoRight.winding_temperature, desired_spline_torque, actpack_current, act_V, N, spline_current, current_ank_angle])
                writer.writerow([current_time_in_stride, vetted_current, act_T_case, exoLeft.thermalModel.T_c, exoLeft.winding_temperature, 0, actpack_current, act_V, 0, spline_current, current_ank_angle])
                
            except KeyboardInterrupt:
                print('Ctrl-C detected, Exiting Gracefully')
                exoLeft.fxs.send_motor_command(exoLeft.dev_id, fxe.FX_CURRENT, 0)
                sleep(0.5)
                break

            except Exception as err:
                print(traceback.print_exc())
                print("Unexpected error in executing inProcedure:", err)
                break
    
