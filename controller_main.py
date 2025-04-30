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
from flexsea import fxEnums as fxe

from opensourceleg.utilities import SoftRealtimeLoop

from src.settings.constants import (
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
        self.active_device_ids = []
        self.active_sides = []
        
    def _get_active_ports(self):
        """
        Opens known active ports (ttyACM0 & ttyACM1) and establishes a connection.
        Also matches device ID to a side (left/right).
        Assigns to self.active_device_ids and self.active_sides.
        Atleast 1 device has to be connected. 
        
        Only connected devices will be controlled. 
        """
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
        """
        Cleanly commands 0A to the motors and closes the FlexSEA connection.
        """
        for device_id in self.active_device_ids:
            self.fxs.send_motor_command(device_id, fxe.FX_CURRENT, 0)
            time.sleep(0.2)
            print(f"Stopped commanding device: {device_id}")
    
        # close the FlexSEA connection
        self.fxs.close_all()
        
    def __enter__(self):
        """
        Enter the context: Set up the devices and start streaming.
        """
        self._get_active_ports()
        
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context: 0A current command and clean up resources.
        
        Arguments:
        - exc_type: The exception type (if an exception occurred).
        - exc_value: The exception value (if an exception occurred).
        - traceback: The traceback object (if an exception occurred).
        """
        # Close the FlexSEA connection
        self._graceful_exit()
        print(" ~~ FlexSEA connection closed ~~ ")
        

if __name__ == '__main__':
    
    exo = DephyEB51Device() # instantiate exoskeleton device
    clock = SoftRealtimeLoop(dt = 1 / FLEXSEA_FREQ) # create a soft real-time loop clock
    
    with exo:
        
        if len(exo.active_sides) != len(exo.active_device_ids):
            raise Exception("Mismatch between sides and device IDs")
        
        for side, device_id in zip(exo.active_sides, exo.active_device_ids):
            exo.fxs.start_streaming(device_id, FLEXSEA_FREQ, False)    
            print("started streaming for device: ", device_id)

            # set gains for each device
            exo.fxs.set_gains(device_id, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)     

            # TODO: instantiate each active exoskeleton object (pass in fxs, device_id, side)
            
        # run the main control loop
        for t in clock:
            try:
                if t < 0.2:
                    print("running main loop")
                    print(f"Time: {t}")
                else:
                    raise Exception("artificial loop time out to test error handling on exit")
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break
            
            except Exception as err:
                print(traceback.print_exc())
                print("Unexpected error in executing main controller:", err)
                break
    