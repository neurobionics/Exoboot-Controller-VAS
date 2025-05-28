import sys
import glob
import serial
from dephyEB51 import DephyEB51Actuator
from src.utils import CONSOLE_LOGGER

def get_active_ports()->list:
    """
    Lists active serial ports.
    Original Implementation in OSL Legacy Library.
    """
    if sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        ports = glob.glob("/dev/tty[A-Za-z]C*")
    elif sys.platform.startswith("darwin"):
        ports = glob.glob("/dev/tty.*")
    elif sys.platform.startswith("win"):
        ports = ["COM%s" % (i + 1) for i in range(256)]
    else:
        CONSOLE_LOGGER.info("Unsupported platform.")
        raise OSError("Unsupported platform.")

    serial_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            serial_ports.append(port)
        except (OSError, serial.SerialException) as err:
            CONSOLE_LOGGER.info(f"Exception raised: {err}")
            pass

    return serial_ports
        
def create_actuators(gear_ratio:float, baud_rate:int, freq:int, debug_level:int)-> dict:
    """
    Detects active ports and determines corresponding side.
    Creates dictionary of active actuators to be used in the exoskeleton robot class.
    Devices open and start streaming upon instantiation.
    """
    
    # get active ports ONLY
    active_ports = get_active_ports()
    CONSOLE_LOGGER.info(f"Active ports: {active_ports}")
    
    # create an actuator instance for each active port (which also opens the port)
    actuators = {}
    for port in active_ports:
        actuator = DephyEB51Actuator(
            port=port,
            baud_rate=baud_rate,
            frequency=freq,
            debug_level=debug_level
        )
        # log device ID of the actuator
        CONSOLE_LOGGER.info(f"Device ID: {actuator.dev_id}")
                
        # assign the actuator in a dict according to side
        actuator.tag = actuator.side
        actuators[actuator.side] = actuator
        CONSOLE_LOGGER.info(f"Actuator created for: {port, actuator.side}")
        CONSOLE_LOGGER.info(f"      MOTOR SIGN: {actuator.motor_sign}")
        CONSOLE_LOGGER.info(f"      ANKLE SIGN: {actuator.ank_enc_sign}")
        
        CONSOLE_LOGGER.info(" ~~ FlexSEA connection initialized, streaming & exo actuators created ~~ ")
        
    return actuators
