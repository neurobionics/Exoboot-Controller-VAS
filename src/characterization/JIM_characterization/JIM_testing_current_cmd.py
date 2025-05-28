import numpy as np
import time, datetime, threading
import sys
import numpy as np
import argparse

from rtplot import client
from src.settings.constants import (ZERO_CURRENT,
                                    MAX_ALLOWABLE_CURRENT,
                                    TR_DATE_FORMATTER,
                                    BAUD_RATE,
                                    FLEXSEA_FREQ,
                                    LOG_LEVEL,
                                    RTPLOT_IP)
from src.custom_logging.LoggingClass import FilingCabinet
from exoboots import DephyExoboots
from opensourceleg.utilities import SoftRealtimeLoop
from src.utils.actuator_utils import create_actuators

if __name__ == "__main__":
    # get user inputs
    parser = argparse.ArgumentParser(description="JIM characterization script")
    parser.add_argument('-current_setpt_mA', type=int, required=True)
    parser.add_argument('-time', type=int, required=True)
    parser.add_argument('-rom', type=str, required=True)
    args = parser.parse_args()

    # get current date & set filename & directory for saving data
    curr_date = datetime.datetime.today().strftime(TR_DATE_FORMATTER) # Get YEAR_MONTH_DAY_HOUR_MINUTE
    date = curr_date if curr_date else datetime.datetime.today().strftime(TR_DATE_FORMATTER)

    fname = "{}mA".format(args.current_setpt_mA)
    filingcabinet = FilingCabinet("JIM_testing", fname)

    # detect active serial ports & create actuator objects
    actuators = create_actuators(1, BAUD_RATE, FLEXSEA_FREQ, LOG_LEVEL)

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

    # tell the server to initialize the plot
    client.initialize_plots(plot_config)

    # set-up the soft real-time loop:
    clock = SoftRealtimeLoop(dt = 1/250)

    # TODO: setup logger

    # TODO: track vars: time, N, motor current, motor ankle, ankle angle, IMU data, temperature

    with exoboots:

        exoboots.setup_control_modes()

        for _t in clock:
            try:
                # update robot sensor states
                exoboots.update()

                # Command the exo to peak set point current & hold for specified duration
                # Ramp to torque linearly
                ramp_start = time.time()
                ramp_period = 1.0

                while time.time() - ramp_start < ramp_period:
                    ramp_current = args.current_setpt_mA * (time.time()-ramp_start)/ramp_period
                    device.command_motor_current(exothread.motor_sign * int(ramp_current))
                    time.sleep(0.05)
                print("END_RAMP")

                device.command_motor_current(exothread.motor_sign * args.current_setpt_mA)

                while (time.perf_counter() - start_time < args.time) and quit_event.is_set():
                    curr_current = logger.get(exothread.name, "motor_current")
                    curr_temp_exo = logger.get(exothread.name, "temperature")
                    curr_ank_ang = logger.get(exothread.name, "ankle_angle")
                    # print("temp is ",curr_temp_exo)
                    # print("current is ",curr_current)

                    plot_data_array = [abs(curr_current), abs(curr_temp_exo), curr_ank_ang]
                    client.send_array(plot_data_array) # Send data to server to plot

                    # thermal safety shutoff
                    if curr_temp_exo >= MAX_CASE_TEMP:
                        print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
                        quit_event.clear()

                    time.sleep(1/500) #TODO main loop freq variable required

                # update real-time plots & send data to server
                data_to_plt = exoboots.update_JIM_rt_plots()
                client.send_array(data_to_plt)

            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                break

            except Exception as err:
                print("Unexpected error in executing main controller:", err)
                break


    # frequency = 1000
    # for side, device in zip(sides, devices):
    #     if device:
    #         device.start_streaming(frequency)
    #         device.set_gains(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, 0, 0, DEFAULT_FF)

    #         file_prefix = "{}_{}".format(fname, args.rom)
    #         logger = LoggingNexus(fname, file_prefix, filingcabinet, exothread)
    #         log_event.set()

    #         start_time = time.perf_counter()
    #         try:
    #             # Command the exo to peak set point current & hold for specified duration
    #             # Ramp to torque linearly
    #             ramp_start = time.time()
    #             ramp_period = 1.0
    #             while time.time() - ramp_start < ramp_period:
    #                 ramp_current = args.current_setpt_mA * (time.time()-ramp_start)/ramp_period
    #                 device.command_motor_current(exothread.motor_sign * int(ramp_current))
    #                 time.sleep(0.05)
    #             print("END_RAMP")
    #             device.command_motor_current(exothread.motor_sign * args.current_setpt_mA)

    #             while (time.perf_counter() - start_time < args.time) and quit_event.is_set():
    #                 curr_current = logger.get(exothread.name, "motor_current")
    #                 curr_temp_exo = logger.get(exothread.name, "temperature")
    #                 curr_ank_ang = logger.get(exothread.name, "ankle_angle")
    #                 # print("temp is ",curr_temp_exo)
    #                 # print("current is ",curr_current)

    #                 plot_data_array = [abs(curr_current), abs(curr_temp_exo), curr_ank_ang]
    #                 client.send_array(plot_data_array) # Send data to server to plot

    #                 # thermal safety shutoff
    #                 if curr_temp_exo >= MAX_CASE_TEMP:
    #                     print("Case Temperature has exceed 75°C soft limit. Exiting Gracefully")
    #                     quit_event.clear()

    #                 time.sleep(1/500) #TODO main loop freq variable required
    #         except KeyboardInterrupt:
    #             print("KB DONE")
    #         finally:
    #             print("Closing")
    #             # after which, stop logging and dump written contents into csv
    #             log_event.clear()
    #             logger.log()

    #             # after which, stop commanding the motor
    #             device.command_motor_current(0)
    #             device.stop_motor()
