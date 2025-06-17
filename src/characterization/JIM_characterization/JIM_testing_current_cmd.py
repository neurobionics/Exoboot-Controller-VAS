import numpy as np
import datetime
import sys, os, time
import numpy as np

from rtplot import client
from opensourceleg.utilities import SoftRealtimeLoop
from opensourceleg.logging import Logger, LogLevel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.settings.constants import (TR_DATE_FORMATTER,
                                    EXO_SETUP_CONST,
                                    IP_ADDRESSES)
from src.custom_logging.LoggingClass import FilingCabinet, LoggingNexus
from exoboots import DephyExoboots
from src.utils.actuator_utils import create_actuators
from JIM_utils import JIM_data_plotter

class userInputTest():
    def __init__(self):
        """
        Class to Device using User Inputs.
        """
        self.current_setpt_mA = input("current setpoint in mA?: ")
        self.time = input("time in sec: ")
        self.rom = input("rom: ")
        self.dps = input("speed in °/s: " )
        self.alignment_event_time = input("alignment time in sec: " )

if __name__ == "__main__":
    # get user inputs
    args = userInputTest()

    # detect active serial ports & create actuator objects
    actuators = create_actuators(1, EXO_SETUP_CONST.BAUD_RATE, EXO_SETUP_CONST.FLEXSEA_FREQ, EXO_SETUP_CONST.LOG_LEVEL)

    # assign actuators to Exoboots Robot
    exoboots = DephyExoboots(
        tag="exoboots",
        actuators=actuators,
        sensors={}
    )

    # get current date & set filename & directory for saving data
    curr_date = datetime.datetime.today().strftime(TR_DATE_FORMATTER) # Get YEAR_MONTH_DAY
    date = curr_date if curr_date else datetime.datetime.today().strftime(TR_DATE_FORMATTER)

    file_prefix = "{}mA".format(args.current_setpt_mA)
    file_suffix = "{}dps".format(args.dps)
    fname = "{}_{}_{}rom_{}".format(exoboots.detect_active_actuators(), file_prefix, args.rom, file_suffix)
    folder_name = "JIM_testing_{}".format(date)
    filingcabinet = FilingCabinet(folder_name, fname)

    # get location of folder path
    log_path = os.path.abspath(filingcabinet.getpfolderpath())
    logger = Logger(log_path=log_path,
                    file_name=fname,
                    buffer_size=10*EXO_SETUP_CONST.FLEXSEA_FREQ,
                    file_level = LogLevel.DEBUG,
                    stream_level = LogLevel.INFO,
                    enable_csv_logging = True
                )

    # set-up real-time plots:
    JIM_data_plotter = JIM_data_plotter(exoboots.actuators)
    client.configure_ip(IP_ADDRESSES.RTPLOT_IP)
    plot_config = JIM_data_plotter.initialize_JIM_rt_plots()
    client.initialize_plots(plot_config)

    # set-up the soft real-time loop:
    clock = SoftRealtimeLoop(dt = 1/850)

    # track vars: time, N, motor current, ankle angle, temperature
    JIM_data_plotter.track_variables_for_JIM_logging(logger)

    ramp_period:float = 1.0

    with exoboots:

        exoboots.setup_control_modes()

        # setup dict of current setpoints depending on active actuators
        exoboots.create_current_setpts_dict()

        for t in clock:
            try:
                # update robot sensor states
                exoboots.update()

                if (t > 0.0) and (t <= float(args.alignment_event_time)):
                    exoboots.set_to_transparent_mode()
                    print(f"in transparent mode")

                elif (t > float(args.alignment_event_time)) and (t <= ramp_period):
                    print(f"{args.alignment_event_time} SEC SLEEP COMPLETED.")
                    # ramp to torque linearly
                    ramp_current = float(args.current_setpt_mA) * t/ramp_period
                    exoboots.update_current_setpoints(current_inputs=ramp_current, asymmetric=False)
                    exoboots.command_currents()

                elif (t > ramp_period) and (t <= float(args.time)):

                    print(f"RAMP COMPLETED. Current setpoint is now {args.current_setpt_mA} mA")
                    # Command the exo to peak set point current & hold for specified duration
                    exoboots.update_current_setpoints(current_inputs=int(args.current_setpt_mA), asymmetric=False)
                    exoboots.command_currents()

                    # send data to server & update real-time plots
                    data_to_plt = JIM_data_plotter.update_JIM_rt_plots()
                    client.send_array(data_to_plt)

                else:
                    exoboots.set_to_transparent_mode()
                    break

                logger.update()
                logger.flush_buffer()

            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                logger.flush_buffer()
                logger.close()
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                logger.flush_buffer()
                logger.close()
                break