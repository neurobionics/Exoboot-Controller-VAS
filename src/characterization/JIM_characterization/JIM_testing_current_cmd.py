import numpy as np
import datetime
import sys, os
import numpy as np
import argparse

from rtplot import client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.settings.constants import (TR_DATE_FORMATTER,
                                    BAUD_RATE,
                                    FLEXSEA_FREQ,
                                    LOG_LEVEL,
                                    RTPLOT_IP)
from src.custom_logging.LoggingClass import FilingCabinet
from exoboots import DephyExoboots
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils.actuator_utils import create_actuators

class userInputTest():
    def __init__(self):
        """
        Class to test Device using User Inputs.
        """
        self.current_setpt_mA = input("current setpoint in mA?: ")
        self.time = input("time in sec: ")
        self.rom = input("rom: ")

if __name__ == "__main__":
    # get user inputs
    # parser = argparse.ArgumentParser(description="JIM characterization script")
    # parser.add_argument('-current_setpt_mA', type=int, required=True)
    # parser.add_argument('-time', type=int, required=True)
    # parser.add_argument('-rom', type=str, required=True)
    # args = parser.parse_args()

    args = userInputTest()

    # get current date & set filename & directory for saving data
    curr_date = datetime.datetime.today().strftime(TR_DATE_FORMATTER) # Get YEAR_MONTH_DAY
    date = curr_date if curr_date else datetime.datetime.today().strftime(TR_DATE_FORMATTER)

    fname = "{}mA".format(args.current_setpt_mA)
    filingcabinet = FilingCabinet("JIM_testing", fname)

    # detect active serial ports & create actuator objects
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL) # TODO: remove hardcoded TR filepath

    # assign actuators to Exoboots Robot
    exoboots = DephyExoboots(
        tag="exoboots",
        actuators=actuators,
        sensors={}
    )

    # set-up real-time plots:
    client.configure_ip(RTPLOT_IP)
    plot_config = exoboots.initialize_JIM_rt_plots()
    client.initialize_plots(plot_config)

    # set-up the soft real-time loop:
    clock = SoftRealtimeLoop(dt = 1/250)

    # TODO: setup logger

    # TODO: track vars: time, N, motor current, motor ankle, ankle angle, IMU data, temperature

    ramp_period:float = 1.0

    with exoboots:

        exoboots.setup_control_modes()

        # setup dict of current setpoints depending on active actuators
        current_setpoints = exoboots.create_current_setpts_dict()

        for t in clock:
            try:
                # update robot sensor states
                exoboots.update()

                # ramp to torque linearly
                if t < ramp_period:
                    ramp_current = float(args.current_setpt_mA) * t/ramp_period
                    # TODO: feed in currents into dict (default: both)
                    current_setpoints
                    exoboots.command_currents(int(ramp_current))    # exoboots.left.motor_sign * args.current_setpt_mA

                print("END_RAMP")

                # Command the exo to peak set point current & hold for specified duration
                exoboots.command_currents()
                if (t >= ramp_period) and (t <= args.time):
                    # TODO: log variables (motor current, temp, ankle angle)

                    # send data to server & update real-time plots
                    data_to_plt = exoboots.update_JIM_rt_plots()
                    client.send_array(data_to_plt)

            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break