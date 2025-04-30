import numpy as np
import os, sys, csv, time, datetime, threading
import sys
import numpy as np
import argparse

from flexsea.device import Device
from rtplot import client 
from constants import ZERO_CURRENT, MAX_ALLOWABLE_CURRENT, DEV_ID_TO_SIDE_DICT,DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_FF, TR_DATE_FORMATTER, MAX_CASE_TEMP
from src.custom_logging.LoggingClass import LoggingNexus, FilingCabinet
from ExoClass_thread import ExobootThread


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
    if side_1 == 'left' or side_2 == 'right':
        return side_1, device_1, side_2, device_2
    elif side_1 == "right" or side_2 == "left":
        return side_2, device_2, side_1, device_1
    else:
        raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")
            
     
if __name__ == "__main__":
    # user inputs
    parser = argparse.ArgumentParser(description="JIM characterization script")
    parser.add_argument('-current_setpt_mA', type=int, required=True)
    parser.add_argument('-time', type=int, required=True)
    parser.add_argument('-rom', type=str, required=True)
    args = parser.parse_args()

    side_left, device_left, side_right, device_right = get_active_ports()
    devices = [device_left, device_right]
    sides = [side_left, side_right]
    
    # Get current date
    curr_date = datetime.datetime.today().strftime(TR_DATE_FORMATTER) # Get YEAR_MONTH_DAY_HOUR_MINUTE
    date = curr_date if curr_date else datetime.datetime.today().strftime(TR_DATE_FORMATTER)
    
    fname = "{}mA".format(args.current_setpt_mA)
    filingcabinet = FilingCabinet("JIM_testing", fname)
    
    # Initialize rtplot timeseries
    client.configure_ip("35.3.69.66") # ip address of computer that is plotting data (server)
    
    plot_1_config = {'names': ['Current (mA)'],
                    'title': "Current (mA) vs. Sample",
                    'ylabel': "Current (mA)",
                    'xlabel': 'timestep', 
                    'yrange': [args.current_setpt_mA-100, args.current_setpt_mA+100],
                    "colors":['r'],
                    "line_width": [8,8],
                    }
    plot_2_config = {'names': ['Temp (°C)'],
                    'title': "Temp (°C) vs. Sample",
                    'ylabel': "Temperature (°C)",
                    'xlabel': 'timestep', 
                    'yrange': [30, 50],
                    "colors":['b'],
                    "line_width": [8,8],
                    }
    plot_3_config = {'names':['Ankle Angle (°)'],
                    'title': "Ankle Angle (°) vs. Sample",
                    'ylabel': "Ankle Angle (°)",
                    'xlabel': 'timestep',
                    'yrange': [0, 150],
                    "colors":['g'],
                    "line_width": [8,8],
                    }

    plot_config = [plot_1_config, plot_2_config, plot_3_config]

    # Tell the server to initialize the plot
    client.initialize_plots(plot_config)
  
    frequency = 1000
    for side, device in zip(sides, devices):
        if device:
            device.start_streaming(frequency)
            device.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)
            
            # Thread events
            quit_event = threading.Event()
            pause_event = threading.Event()
            log_event = threading.Event()
            quit_event.set()
            
            # Start with threads paused
            pause_event.clear() 
            log_event.clear()
            
            # Create Exoboot Thread:
            exothreadname = "exothread_{}".format(side)
            exothread = ExobootThread(side, device, 0, exothreadname, True, quit_event, pause_event, log_event, True, ZERO_CURRENT, MAX_ALLOWABLE_CURRENT, on_pause_triggers=0)
            exothread.start()
            
            file_prefix = "{}_{}".format(fname, args.rom)
            logger = LoggingNexus(fname, file_prefix, filingcabinet, exothread)
            log_event.set()
            
            start_time = time.perf_counter()
            try:
                # Command the exo to peak set point current & hold for specified duration
                # Ramp to torque linearly
                ramp_start = time.time()
                ramp_period = 1.0
                while time.time() - ramp_start < ramp_period:
                    ramp_current = args.current_setpt_mA * (time.time()-ramp_start)/ramp_period
                    device.command_motor_current(exothread.motor_sign * int(ramp_current))
                    time.sleep(0.05)
                print("END_RAMP")
                device.command_motor_current(exothread.motor_sign * args.current_setpt_mA)
                
                while (time.perf_counter() - start_time < args.time) and quit_event.is_set():                    
                    curr_current = logger.get(exothread.name, "motor_current")
                    curr_temp_exo = logger.get(exothread.name, "temperature")
                    curr_ank_ang = logger.get(exothread.name, "ankle_angle")
                    # print("temp is ",curr_temp_exo)
                    # print("current is ",curr_current)
                    
                    plot_data_array = [abs(curr_current), abs(curr_temp_exo), curr_ank_ang]
                    client.send_array(plot_data_array) # Send data to server to plot
                    
                    # thermal safety shutoff
                    if curr_temp_exo >= MAX_CASE_TEMP:
                        print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
                        quit_event.clear()
                    
                    time.sleep(1/500) #TODO main loop freq variable required
            except KeyboardInterrupt:
                print("KB DONE")
            finally:
                print("Closing")
                # after which, stop logging and dump written contents into csv
                log_event.clear()
                logger.log()
                
                # after which, stop commanding the motor
                device.command_motor_current(0)
                device.stop_motor()
