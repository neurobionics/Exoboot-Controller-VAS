"""
Description: 

This script is the main controller for the Dephy EB-51 Exoskeletons.
It is responsible for initializing the exoskeletons and running the main control loop.

NOTE: 
This script deliberately uses the downgraded 8.0.1 flexsea library.
The newer flexsea libraries have an integer overflow issue, preventing 
new sensor data from being received. This issue only exists for the exoskeleton devices
(not the actpacks). The 8.0.1 library is stable with a Raspberry Pi 4B with a 32-bit OS, 
using python 3.9.

Date: 04/29/2025
Author(s): Nundini Rawal
"""

import sys, time, traceback

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging.logger import Logger
from opensourceleg.actuators.dephy import DephyLegacyActuator

from .src.settings.constants import (
    BAUD_RATE,
    DEV_ID_TO_SIDE_DICT,
    FLEXSEA_FREQ,
    DEFAULT_KP,
    DEFAULT_KI,
    DEFAULT_KD,
    DEFAULT_FF,
    KNOWN_PORTS, 
    LOG_LEVEL
)
    
class DephyEB51Device():
    def __init__(self):
        self.fxs = flex.FlexSEA()     # instantiate the flexsea actuator package
        
    def get_active_ports_old(self):
        """
        Opens known active ports (ttyACM0 & ttyACM1) and establishes a connection 
        with devices. Also matches device ID to a side (left/right).
        
        Atleast 1 device has to be connected. Only connected devices will be controlled. 
        
        arguments:
        - None
        
        returns:
        - dev_id: device ID of the exoskeleton
        - side: side of the exoskeleton (left/right)
        """
        try:
            # obtain device ID
            dev_id_1 = fxs.open(port="/dev/ttyACM0", baud_rate=BAUD_RATE, log_level=3)
            
            # determine which side the device_id corresponds to
            side_1 = DEV_ID_TO_SIDE_DICT[dev_id_1]
            
            print("Device 1: {}, {}".format(dev_id_1, side_1))
        except:
            side_1 = None
            dev_id_1 = None
            print("DEVICE 1 NOT FOUND")
            
        try:
            # obtain device ID
            dev_id_2 = fxs.open(port="/dev/ttyACM1", baud_rate=BAUD_RATE, log_level=3)
            
            # determine which side the device_id corresponds to
            side_2 = DEV_ID_TO_SIDE_DICT[dev_id_2]
            
            print("Device 1: {}, {}".format(dev_id_2, side_2))
        except:
            side_2 = None
            dev_id_2 = None
            print("DEVICE NOT FOUND: ")
        
        # if neither exoboots are connected, exit the program
        if not (dev_id_1 or dev_id_2):
            sys.exit("NO DEVICES: CONNECT AND POWER ON ATLEAST 1 EXOBOOT")

        # always assign first pair of outputs to left side
        if side_1 == "left" or side_2 == "right":
            return side_1, dev_id_1, side_2, dev_id_2
        elif side_1 == "right" or side_2 == "left":
            return side_2, dev_id_2, side_1, dev_id_1
        else:
            raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")

    def _get_active_ports(self):
        self.active_device_ids = []
        self.active_sides = []
        for port in KNOWN_PORTS:
            try:
                dev_id = self.fxs.open(port=port, baud_rate=BAUD_RATE, log_level=LOG_LEVEL)
                side = DEV_ID_TO_SIDE_DICT[dev_id]
                print(f"Device on {port}: {dev_id}, {side}")
                self.active_device_ids.append(dev_id)
                self.active_sides.append(side)
            except:
                print(f"DEVICE NOT FOUND: {port}")
            
        # exit if no devices are connected
        if not self.active_device_ids:
            sys.exit("NO DEVICES: CONNECT AND POWER ON AT LEAST 1 EXOBOOT")
        
        print(" ~~ FlexSEA connection initialized ~~ ")
    
    def _graceful_exit(self):
        self.fxs.send_motor_command(self.dev_id, fxe.FX_CURRENT, 0)
        time.sleep(0.5)
    
        self.fxs.close_all()
        
    def __enter__(self):
        self._get_active_ports()
        
    def __exit__(self, exc_type, exc_value, traceback):
        # Close the FlexSEA connection
        self._graceful_exit()
        print("FlexSEA connection closed.")
        

if __name__ == '__main__':
    
    sensor_logger = Logger(log_path="./osl_logs",file_name="reading_sensor_data")
    clock = SoftRealtimeLoop(dt = 1 / FLEXSEA_FREQ)
    
    exo = DephyEB51Device()
    
    with exo:
        for side, device_id in zip(exo.active_sides, exo.active_device_ids):
            # start streaming device data
            exo.fxs.start_streaming(device_id, FLEXSEA_FREQ, False)    
            print("started streaming for device: ", device_id)
            
            # set device current control gains
            device_id.set_gains(device_id, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)     
            print("set gains for: ", device_id)

            # TODO: instantiate each active exoskeleton object (pass in fxs, device_id, side)
            
        # run the main control loop
        for t in clock:
            try:
                print("running main loop")
                print(f"Time: {t}")
                
                # TODO: test sensor_logger
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break
            
            except Exception as err:
                print(traceback.print_exc())
                print("Unexpected error in executing main controller:", err)
                break
    