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

from opensourceleg.logging import Logger, LogLevel
from opensourceleg.utilities import SoftRealtimeLoop

from exoboots import DephyExoboots
from src.utils.actuator_utils import create_actuators
from src.utils.filing_utils import get_logging_info
from src.settings.constants import(
    BAUD_RATE,
    FLEXSEA_FREQ,
    LOG_LEVEL
)

def track_variables_for_logging(logger: Logger) -> None:
    """
    Track various variables for logging.
    """
    dummy_grpc_value = 5.0
    logger.track_variable(lambda: dummy_grpc_value, "dollar_value")
    logger.track_variable(lambda: ankle_torque_setpt, "torque_setpt_Nm")
    
    logger.track_variable(lambda: exoboots.left.accelx, "accelx_mps2")
    logger.track_variable(lambda: exoboots.left.motor_current, "current_mA")
    logger.track_variable(lambda: exoboots.left.motor_position, "position_rad")
    logger.track_variable(lambda: exoboots.left.motor_encoder_counts, "encoder_counts")
    logger.track_variable(lambda: exoboots.left.case_temperature, "case_temp_C")
    

if __name__ == '__main__':
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)

    exoboots = DephyExoboots(
        tag="exoboots", 
        actuators=actuators, 
        sensors={}
    )

    clock = SoftRealtimeLoop(dt = 1 / 1) 
    
    log_path, file_name = get_logging_info(use_input_flag=False)
    data_logger = Logger(log_path=log_path, file_name=file_name, buffer_size=10*FLEXSEA_FREQ, file_level = LogLevel.DEBUG, stream_level = LogLevel.INFO)
    track_variables_for_logging(data_logger)
    
    # TODO: instantiate an assistance generator
    
    with exoboots:
        
        exoboots.setup_control_modes()
        
        # spool belts upon startup
        exoboots.spool_belts()
        
        # specify a ankle torque setpoint
        ankle_torque_setpt = 20 # Nm
            
        for _t in clock:
            try:
                # update robot sensor states
                exoboots.update()
                
                # TODO: determine current gait state
                
                
                
                # TODO: determine appropriate torque setpoint using assistance generator
                
                
                # determine appropriate current setpoint that matches the torque setpoint (updates transmission ratio internally)
                currents = exoboots.find_current_setpoints(ankle_torque_setpt)
                
                # command appropriate current setpoint (internally ensures that current in mA is a integer)
                exoboots.command_currents(currents)
                
                # TODO: receive any NEW grpc values/inputs for next iteration
                
                
                # record current values to buffer, log to file, then flush the buffer
                data_logger.update()
                data_logger.flush_buffer()
                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                data_logger.close()
                break
            
            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                data_logger.close()
                break