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

def get_active_ports(fxs):
    """
    Scans and returns a list of active ports corresponding to each exoskeleton 
    """
    
    
    
    return flex.get_active_ports()
    


if __name__ == '__main__':
    
    # initialize the flexsea library
    fxs = flex.FlexSEA()
  
    # get active ports
    active_ports = get_active_ports(fxs)
    print(f"Active ports: {active_ports}")