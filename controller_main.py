# Description: 
#
# This script is the main controller for the Dephy EB-51 Exoskeletons.
# It is responsible for initializing the exoskeletons and running the main control loop.
#
# NOTE: 
# This script deliberately uses the downgraded 8.0.1 flexsea library.
# The newer flexsea libraries have an integer overflow issue, preventing new sensor data to be received.
# This issue only exists for the Exoskeleton devices. 
# The 8.0.1 library is stable with a Raspberry Pi 4B and 32-bit OS, using python 3.9.
#
# Date: 04/29/2025

from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging.logger import Logger
from opensourceleg.actuators.dephy import DEFAULT_POSITION_GAINS, DephyActuator

from .src.settings.constants import BAUD_RATE, DEV_ID_TO_SIDE_DICT

class MainController:
    def __init__(self):
        self.fxs = flex.FlexSEA()     # instantiate the flexsea library
    

    def get_active_ports(self):
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
            dev_id_1 = self.fxs.open(port="/dev/ttyACM0", baud_rate=BAUD_RATE, log_level=3)
            
            # determine which side the device_id corresponds to
            side_1 = DEV_ID_TO_SIDE_DICT[dev_id_1]
            
            print("Device 1: {}, {}".format(dev_id_1, side_1))
        except:
            side_1 = None
            dev_id_1 = None
            print("DEVICE 1 NOT FOUND")
            
        try:
            # obtain device ID
            dev_id_2 = self.fxs.open(port="/dev/ttyACM1", baud_rate=BAUD_RATE, log_level=3)
            
            # determine which side the device_id corresponds to
            side_2 = DEV_ID_TO_SIDE_DICT[dev_id_2]
            
            print("Device 1: {}, {}".format(dev_id_2, side_2))
        except:
            side_2 = None
            dev_id_2 = None
            print("DEVICE 2 NOT FOUND")
       

        # if neither exoboots are connected, exit the program
        if not (dev_id_1 or dev_id_2):
            print("\nNO DEVICES: CONNECT AND POWER ON ATLEAST 1 EXOBOOT\n")
            quit()

        # always assign first pair of outputs to left side
        if side_1 == "left" or side_2 == "right":
            return side_1, dev_id_1, side_2, dev_id_2
        elif side_1 == "right" or side_2 == "left":
            return side_2, dev_id_1, side_1, dev_id_2
        else:
            raise Exception("Invalid sides for devices: Check DEV_ID_TO_SIDE_DICT!")
    
    def run(self):
        side_1, dev_id_1, side_2, dev_id_2 = self.get_active_ports()    # open & connect to devices
        
        # TODO: instantiate each exoskeleton object
        
        # TODO: start streaming device, set gains
        
        # TODO:spool belts
        
        # iterate though FSM Controller
        
        # exit gracefully either via keyboard interrupt or by exiting the program
        

if __name__ == '__main__':
    MainController.run()
    