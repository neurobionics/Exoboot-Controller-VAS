import sys, glob, serial
from opensourceleg.actuators.dephy import DephyLegacyActuator
from src.settings.constants import DEV_ID_TO_SIDE_DICT

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
        raise OSError("Unsupported platform.")

    serial_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            serial_ports.append(port)
        except (OSError, serial.SerialException):
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
    print(f"Active ports: {active_ports}")
    
    # create an actuator instance for each active port (which also opens the port)
    actuators = {}
    for port in active_ports:
        try:
            actuator = DephyLegacyActuator(
                port=port,
                baud_rate=baud_rate,
                frequency=freq,
                debug_level=debug_level
            )
            
            # get device ID of the actuator
            dev_id = actuator.report_dev_id()
            print(f"Device ID: {dev_id}")
            
            # get the corresponding side of the actuator
            active_side = assign_id_to_side(dev_id)
            print(f"Active side: {active_side}")
            
            # assign the actuator in a dict according to side
            actuator._tag = active_side
            actuators[active_side] = actuator
            
            print(f"Actuator created for: {port, active_side}")
        except:
            print(f"DEVICE NOT FOUND for port: {port}, so failed to create {active_side} actuator.")
        
        # exit if no devices are connected
        if not actuators:
            sys.exit("NO DEVICES: CONNECT AND POWER ON AT LEAST 1 EXOBOOT")
        
        print(" ~~ FlexSEA connection initialized, streaming & exo actuators created ~~ ")
        
    return actuators
    
def assign_id_to_side(dev_id: int)-> str:
    """
    Determines side (left/right) of the actuator based on previously mapped device ID number.
    """
    side = DEV_ID_TO_SIDE_DICT[dev_id]
    
    return side
    