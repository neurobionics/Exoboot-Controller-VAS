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

from opensourceleg.utilities import SoftRealtimeLoop
from exoboots import DephyExoboots, create_actuators
from src.settings.constants import(
    BAUD_RATE,
    FLEXSEA_FREQ,
    LOG_LEVEL
)

if __name__ == '__main__':
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    sensors = {}

    exoboots = DephyExoboots(
        tag="exoboots", 
        actuators=actuators, 
        sensors=sensors
    )

    clock = SoftRealtimeLoop(dt = 1 / 100) 

    with exoboots:
        
        exoboots.setup_controller()
            
        for t in clock:
            try:
                print(f"Time: {t:.2f} seconds")
                
                # TODO: Add control logic here
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break