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
from rtplot import client 

from opensourceleg.logging import Logger, LogLevel
from opensourceleg.utilities import SoftRealtimeLoop

from exoboots import DephyExoboots
from src.utils.actuator_utils import create_actuators
from src.utils.filing_utils import get_logging_info
from src.settings.constants import(
    BAUD_RATE,
    FLEXSEA_FREQ,
    LOG_LEVEL,
    RTPLOT_IP
)

if __name__ == '__main__':
    # ask for trial type before connecting to actuators to allow for mistakes in naming and --help usage
    log_path, file_name = get_logging_info(use_input_flag=True)

    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)
    print(f"Actuators: {actuators}")
    sensors = {}

    exoboots = DephyExoboots(
        tag="exoboots", 
        actuators=actuators, 
        sensors=sensors
    )

    # set-up the soft real-time loop:
    clock = SoftRealtimeLoop(dt = 1 / 1) 
    
    # set-up logging:
    logger = Logger(log_path=log_path,
                    file_name=file_name,
                    buffer_size=10*FLEXSEA_FREQ,
                    file_level = LogLevel.DEBUG,
                    stream_level = LogLevel.INFO
                    )
    exoboots.track_variables_for_logging(logger)
    
    # set-up real-time plots:
    client.configure_ip(RTPLOT_IP)
    plot_config = exoboots.initialize_rt_plots()
    client.initialize_plots(plot_config)
    
    with exoboots:
        
        exoboots.setup_control_modes()
            
        for _t in clock:
            try:
                # update robot sensor states
                exoboots.update()
                
                # TODO: Add control logic here
                
                # record current values to buffer, log to file, then flush the buffer
                logger.update()
                
                # update real-time plots & send data to server
                data_to_plt = exoboots.update_rt_plots()
                client.send_array(data_to_plt)
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                logger.close()
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                logger.close()
                break