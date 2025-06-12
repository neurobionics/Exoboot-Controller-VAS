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

# TODO: fix this console logger import
CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )
from src.settings.constants import (
    EXO_SETUP_CONST,
    IP_ADDRESSES,
    INCLINE_WALK_TIMINGS
)

from gse_bertec import Bertec_Estimator
from gse_imu import IMU_Estimator
from src.exo.gait_state_estimator.forceplate.ZMQ_PubSub import Subscriber
from src.exo.assistance_calculator import AssistanceCalculator

if __name__ == '__main__':
    # ask for trial type before connecting to actuators to allow for mistakes in naming and --help usage
    log_path, file_name = get_logging_info(user_input_flag=False)

    actuators = create_actuators(1, EXO_SETUP_CONST.BAUD_RATE, EXO_SETUP_CONST.FLEXSEA_FREQ, EXO_SETUP_CONST.LOG_LEVEL)

    exoboots = DephyExoboots(
        tag="exoboots",
        actuators=actuators,
        sensors={}
    )

    # set-up assistance calculator:
    assistance_calculator = AssistanceCalculator()

    # create a set of peak torques to test (must be <= 5Nm)
    peak_torque = input("peak torque to test (Nm); must be <= 5Nm: ")
    try:
        peak_torque = float(peak_torque)
        if peak_torque > 5.0:
            raise ValueError("Peak torque must be less than or equal to 5Nm.")
    except ValueError as e:
        print(f"Invalid input for peak torque: {e}")
        sys.exit(1)
    stride_time = 1.2
    time_in_stride = 0.0
    in_swing_flag = False
    torque_command = 0.0

    # TODO: instantiate FSM for exoboots ~ swing, stance, passive

    # set-up the soft real-time loop:
    clock = SoftRealtimeLoop(dt = 1/EXO_SETUP_CONST.FLEXSEA_FREQ)

    # set-up logging:
    logger = Logger(log_path=log_path,
                    file_name=file_name+"_incline",
                    buffer_size=10*EXO_SETUP_CONST.FLEXSEA_FREQ,
                    file_level = LogLevel.DEBUG,
                    stream_level = LogLevel.INFO
                    )
    exoboots.track_variables_for_logging(logger)

    # track Assistance Calculator variables
    logger.track_variable(lambda: time_in_stride, "time_in_stride_s")
    logger.track_variable(lambda: torque_command, "torque_setpt_Nm")
    logger.track_variable(lambda: assistance_calculator.percent_stride, "percent_gait_cycle")
    logger.track_variable(lambda: in_swing_flag, "in_swing_flag_bool")

    # TODO: add in GSE's
    sub_bertec_left = Subscriber(publisher_ip=IP_ADDRESSES.VICON_IP,topic_filter='fz_left',timeout_ms=5)
    bertec_estimator = Bertec_Estimator(zmq_subscriber=sub_bertec_left)
    imu_estimator = IMU_Estimator()

    logger.track_variable(lambda: int(not bertec_estimator.in_contact), "in_swing")
    logger.track_variable(lambda: int(imu_estimator.activation_state), "activation_state")
    logger.track_variable(lambda: bertec_estimator.force_prev, "forceplate")

    # set-up real-time plots:
    client.configure_ip(IP_ADDRESSES.RTPLOT_IP)
    plot_config = exoboots.initialize_rt_plots()
    client.initialize_plots(plot_config)

    with exoboots:

        exoboots.setup_control_modes()

        # spool belts upon startup
        # exoboots.spool_belts()

        for _t in clock:
            try:

                # update robot sensor states
                exoboots.update()

                # TODO: determine current gait state

                # Simulated in_swing_flag based on percent_stride
                if assistance_calculator.percent_stride > INCLINE_WALK_TIMINGS.P_TOE_OFF:
                    in_swing_flag = True
                else:
                    in_swing_flag = False

                # Simulated time in stride (in seconds)
                if time_in_stride >= stride_time:
                    time_in_stride = 0.0
                else:
                    time_in_stride += 1 / EXO_SETUP_CONST.FLEXSEA_FREQ

                # determined appropriate torque setpoint using assistance generator
                torque_command = assistance_calculator.torque_generator(
                time_in_stride, stride_time, float(peak_torque), in_swing_flag)

                # determine appropriate current setpoint that matches the torque setpoint (updates transmission ratio internally)
                currents = exoboots.find_current_setpoints(torque_command)

                # command appropriate current setpoint (internally ensures that current in mA is a integer)
                exoboots.command_currents(currents)

                # update logger
                logger.update()

                # TODO: receive any NEW grpc values/inputs for next iteration

                # TODO: update GSE's
                imu_estimator.update(exoboots.right.accelx)
                bertec_estimator.update()

                # TODO: Add control logic here

                # update real-time plots & send data to server
                data_to_plt = exoboots.update_rt_plots(not bertec_estimator.in_contact, imu_estimator.activation_state)
                client.send_array(data_to_plt)

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

