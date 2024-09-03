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
import sys

sys.path.insert(0, '/home/pi/Exoboot-Controller-VAS/')
import config

import time
from flexsea.device import Device
from ExoClass import ExoObject
from SoftRTloop import FlexibleTimer

def get_active_ports():
    """To use the exos, it is necessary to define the ports they are going to be connected to. 
    These are defined in the ports.yaml file in the flexsea repo.
     """
    # port_cfg_path = '/home/pi/VAS_exoboot_controller/ports.yaml'
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


if __name__ == "__main__":
    # Recieve active ports that the exoskeletons are connected to
    side_1, device_1, side_2, device_2 = get_active_ports()
    print(side_1, device_1.id, side_2, device_2.id)
    
    frequency = 500
    device_1.start_streaming(frequency)
    device_2.start_streaming(frequency)
    device_1.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)
    device_2.set_gains(config.DEFAULT_KP, config.DEFAULT_KI, config.DEFAULT_KD, 0, 0, config.DEFAULT_FF)
    
    if side_1 == "left":
        motor_sign_left = -1
        motor_sign_right = -1
    else:
        motor_sign_left = -1
        motor_sign_right = -1

    # Instantiate exo object for both left and right sides
    if(side_1 == 'left'):
        exo_left = ExoObject(side = side_1, device = device_1)
        exo_right = ExoObject(side = side_2, device = device_2)
    else:
        exo_left = ExoObject(side=side_2, device = device_2)
        exo_right = ExoObject(side=side_1, device = device_1)
    
    input('Press ANY KEY to spool the LEFT exo belt')
    exo_left.spool_belt()
    exo_left.set_spline_timing_params(config.spline_timing_params)

    peak_current = input("Define a peak current amount (in mA): ")
    peak_current = int(peak_current)
    
    if(side_1 == 'left'):
        L_exo_filename = "/home/pi/Exoboot-Controller-VAS/Thermal_Characterization/thermal_fulldata_{}_{}mA.csv".format(side_1, peak_current)
        R_exo_filename = "/home/pi/Exoboot-Controller-VAS/Thermal_Characterization/thermal_fulldata_{}_{}mA.csv".format(side_2, peak_current)
    else:
        L_exo_filename = "/home/pi/Exoboot-Controller-VAS/Thermal_Characterization/thermal_fulldata_{}_{}mA.csv".format(side_2, peak_current)
        R_exo_filename = "/home/pi/Exoboot-Controller-VAS/Thermal_Characterization/thermal_fulldata_{}_{}mA.csv".format(side_1, peak_current)
    
    act_current = np.array([])
    act_T_c = np.array([])
    modelled_T_c = np.array([])
    modelled_T_w = np.array([])
    torques = np.array([])
    array_time_in_current_stride = np.array([])
    motor_currs = np.array([])
    
    input('HIT ANY KEY to COMMENCE Thermal Testing for LEFT Exo ONLY...')
    
    # Iterate through your state machine controller that controls the exos 
    inProcedure = True
    iterations = 0
    current_time_in_stride = 0
    stride = 0
    stride_period = 1.2
    exo_safety_shutoff_flag = False
    
    softRTloop = FlexibleTimer(target_freq = frequency)
    
    # Header
    datapoint_array = [ 'trial_time', 
                        'state_time_left',
                        'loop_freq',
                        'current_time_in_stride',
                        'commanded_current', 
                        'case_temp', 
                        'modelled_winding_temp',
                        'motor_current',
                        'motor_voltage',
                        'current_ank_ang',
                        'battery_volt',
                        'battery_current',
                        'ang_vel']
    
    with open(L_exo_filename, 'a') as fd:
        writer = csv.writer(fd,lineterminator='\n',quotechar='|')
        writer.writerow(datapoint_array)
        
        sim_start_time = time.monotonic()
        trial_start_time = sim_start_time      
        prev_time = sim_start_time
        
        while inProcedure:
            iterations += 1
            curr_time = time.monotonic()
            loop_dt = curr_time - prev_time
            
            if loop_dt >= 0.001:
                print("loop freq: ", 1/loop_dt)
            else:
                loop_dt = 1/frequency

            # os.system('clear')
            try:

                # simulate a gait state estimator: set a fixed stride period & increment by 0,01s
                if current_time_in_stride >= stride_period:
                    current_time_in_stride = 0.0
                    sim_start_time = time.monotonic()
                    stride += 1
                    # print('{} stride(s) completed', stride)
                elif current_time_in_stride < stride_period:
                    current_time_in_stride = time.monotonic() - sim_start_time
                    # print("time in curr stride: ", current_time_in_stride)

                # read from the exoskeleton (testing without Varun's GSE/sensor reading thread)
                act_pack = exo_left.device.read()
                bat_volt = act_pack['batt_volt']/1000       # converting to volts
                bat_curr = act_pack['batt_curr']
                state_time = act_pack['state_time'] / 1000  # converting to seconds
                
                if iterations == 1:
                    state_time_start = act_pack['state_time'] / 1000    # converting to seconds
                
                ang_vel = act_pack['gyroz'] * config.GYRO_GAIN
                current_ank_angle = (exo_left.ank_enc_sign*act_pack['ank_ang'] * exo_left.ANK_ENC_CLICKS_TO_DEG)    # obtain ankle angle in deg wrt max dorsi offset
                current_mot_angle = (motor_sign_left * act_pack['mot_ang'] * exo_left.MOT_ENC_CLICKS_TO_DEG)        # obtain motor angle in deg
                
                spline_current = exo_left.assistance_generator.current_generator_MAIN(current_time_in_stride, stride_period, peak_current, False)
                # print("commanded current: ", spline_current)    # current in terms of mA

                # Check whether commanded current is above the maximum current threshold
                vetted_current = int( max(min(int(spline_current), exo_left.CURRENT_THRESHOLD), exo_left.bias_current) )
                # Current control vetted current:
                exo_left.device.command_motor_current(exo_left.exo_left_or_right_sideMultiplier * vetted_current)
                    
                # determine actual case temperature & motor current
                actpack_current = act_pack['mot_cur']
                act_T_case = act_pack['temperature']
                act_V = act_pack['mot_volt']
                # print("measured case temp: ", act_T_case)
                # print("actpack_current", actpack_current)
                
                # determine modeled case & winding temp
                exo_left.thermalModel.T_c = act_T_case
                exo_left.thermalModel.update(dt=loop_dt, motor_current=actpack_current)
                exo_left.winding_temperature = exo_left.thermalModel.T_w

                # Shut off exo if thermal limits breached
                if act_T_case >= 75:#exo_left.max_case_temperature
                    exo_safety_shutoff_flag = True 
                    print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
                if exo_left.winding_temperature >= exo_left.max_winding_temperature:
                    exo_safety_shutoff_flag = True 
                    print("Winding Temperature has exceed 115°C soft limit. Exiting Gracefully")

                # Shut off the exo motors and exit out of loop gracefully
                if exo_safety_shutoff_flag == True:
                    print("Exiting thermal loop procedure")
                    exo_left.device.command_motor_current(0)
                    
                    # Stop the motors and close the device IDs before quitting
                    exo_left.device.stop_motor() 
                    exo_right.device.stop_motor()
                    """Exit the execution loop"""
                    inProcedure = False

                # write data to csv
                writer.writerow([time.time() - trial_start_time,
                                state_time - state_time_start,
                                1/loop_dt,
                                current_time_in_stride,
                                vetted_current,
                                act_T_case,
                                exo_left.winding_temperature,
                                actpack_current, 
                                act_V,
                                current_ank_angle,
                                bat_volt,
                                bat_curr,
                                ang_vel])
                
                prev_time = curr_time
                softRTloop.pause()
                # time.sleep(1/softRTloop)
                
                
            except KeyboardInterrupt:
                print('Ctrl-C detected, Exiting Gracefully')
                exo_left.device.command_motor_current(0)
                
                # Stop the motors and close the device IDs before quitting
                exo_left.device.stop_motor() 
                exo_right.device.stop_motor()
                
                break

            except Exception as err:
                print(traceback.print_exc())
                print("Unexpected error in executing inProcedure:", err)
                break
    
