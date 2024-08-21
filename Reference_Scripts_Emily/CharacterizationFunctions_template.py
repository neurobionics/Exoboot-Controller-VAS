# Description:
# This script contains functions to home the exoskeletons & to obtain the transmission ratio curve.
#
# Original template created by: Emily Bywater


# Emily Bywater
import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np
from typing import List, Tuple
import matplotlib.pyplot as plt
from scipy import interpolate

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

# conversion factors
degToCount = 45.5111
MOT_ENC_CLICKS_TO_DEG = (
    1 / degToCount
)  # TODO: what is this constant?? Motor-to-enc clicks constant? Varun does not have this...

streamFreq = 1000
data_log = False  # False means no logs will be saved
shouldAutostream = 1
# This makes the loop run slightly faster
debug_logging_level = 6  # 6 is least verbose, 0 is most verbose


def zeroProcedure(
    fxs, dev_id, side: str, port: str, baud_rate: int
) -> Tuple[float, float]:
    """This function holds a current of 1000 mA for 1 second and collects ankle angle.
    If the ankle angle hasn't changed during this time, this is the zero. Otherwise, the 1 second hold repeats.
    Subject should stand still while this is running.

    args:
            side (str): 'left' or 'right'
            port (str): port name
            baud_rate (int): baud rate

    returns:
            motorAngleOffset_deg (float): motor angle offset in degrees
            ankleAngleOffset_deg (float): ankle angle offset in degrees
    """

    # changes direction of motor rotation based on side
    if side == "left" or side == "l":
        exo_left_or_right_sideMultiplier = -1  # spool belt/rotate CCW for left exo
    elif side == "right" or side == "r":
        exo_left_or_right_sideMultiplier = 1  # spool belt/rotate CW for right exo

    pullCurrent = 1000
    iterations = 0
    holdingCurrent = True
    holdCurrent = pullCurrent * exo_left_or_right_sideMultiplier
    run_time_total = 1  # seconds
    moveVec = np.array([])
    motorAngleVec = np.array([])
    ankleAngleVec = np.array([])
    motorAngleOffset_deg = 0
    ankleAngleOffset_deg = 0
    ANK_ENC_CLICKS_TO_DEG = 360 / 16384

    # fxs = flex.FlexSEA()
    # dev_id = fxs.open(port, baud_rate, debug_logging_level)
    # fxs.start_streaming(dev_id, freq=streamFreq, log_en=data_log)
    # app_type = fxs.get_app_type(dev_id)

    sleep(0.5)
    startTime = time()

    while holdingCurrent:
        print("in zeroing loop")
        iterations += 1
        currentTime = time()
        timeSec = currentTime - startTime

        fxu.clear_terminal()
        act_pack = fxs.read_device(dev_id)

        current_mot_angle = (
            act_pack.mot_ang * MOT_ENC_CLICKS_TO_DEG
        )  # convert motor encoder counts to angle in degrees (?)
        current_ank_angle = (
            act_pack.ank_ang * ANK_ENC_CLICKS_TO_DEG
        )  # convert ankle encoder counts to angle in degrees

        current_ank_vel = (
            act_pack.ank_vel / 10
        )  # Dephy multiplies ank velocity by 10 (rad/s)
        current_mot_vel = act_pack.mot_vel

        desCurrent = holdCurrent

        fxs.send_motor_command(dev_id, fxe.FX_CURRENT, desCurrent)

        print("Ankle Angle: {} deg...".format(current_ank_angle))

        # determines whether wearer has moved
        if (abs(current_mot_vel)) > 100 or (abs(current_ank_vel) > 1):
            moveVec = np.append(moveVec, True)
        else:
            moveVec = np.append(moveVec, False)

        motorAngleVec = np.append(motorAngleVec, current_mot_angle)
        ankleAngleVec = np.append(ankleAngleVec, current_ank_angle)

        # if the ankle angle hasn't changed during the hold time, determine offsets and exit loop
        if (timeSec) >= run_time_total:
            if not np.any(moveVec):  # if none moved
                motorAngleOffset_deg = np.mean(motorAngleVec)
                ankleAngleOffset_deg = np.mean(ankleAngleVec)
                holdingCurrent = False

            else:
                print("retrying")
                moveVec = np.array([])
                motorAngleVec = np.array([])
                ankleAngleVec = np.array([])
                startTime = time()
                iterations = 0

    # ramp down
    print("Turning off Zero-ing Procedure Current Control...")
    print("Motor Angle offset: {} deg\n".format((motorAngleOffset_deg)))
    print("Ankle Angle offset: {} deg\n".format((ankleAngleOffset_deg)))
    fxs.send_motor_command(dev_id, fxe.FX_NONE, 0)
    sleep(0.5)

    fxs.close(dev_id)

    return (motorAngleOffset_deg, ankleAngleOffset_deg)


def characterizeTRCurve(
    fxs,
    dev_id,
    side: str,
    port: str,
    baud_rate: int,
    motorAngleOffset_deg: float,
    ankleAngleOffset_deg: float,
) -> Tuple[np.array, np.array, np.array]:
    """This function collects a curve of motor angle vs. ankle angle which is differentiated
    later to get a transmission ratio curve vs. ankle angle. The ankle joint should be moved through
    the full range of motion (starting at extreme plantarflexion to extreme dorsiflexion on repeat)
    while this is running.

    args:
            side (str): 'left' or 'right'
            port (str): port name
            baud_rate (int): baud rate
            motorAngleOffset_deg (float): motor angle offset in degrees
            ankleAngleOffset_deg (float): ankle angle offset in degrees

    returns:
            p (np.array): coefficients of 4th order polynomial fit of the curve
    """
    print(
        "Begin to rotate the ankle joint from extreme plantarflexion to extreme dorsiflexion repeatedly until it stops running"
    )

    inProcedure = True
    motorAngleVec = np.array([])
    ankleAngleVec = np.array([])
    interval = 20  # seconds
    iterations = 0
    startTime = time()
    ANK_ENC_CLICKS_TO_DEG = 360 / 16384

    DEFAULT_KP = 40
    DEFAULT_KI = 400
    DEFAULT_KD = 0
    DEFAULT_FF = 120  # 128 is 100% feedforward

    # changes direction of motor rotation based on side
    if side == "left" or side == "l":
        exo_left_or_right_sideMultiplier = -1  # spool belt/rotate CCW for left exo
    elif side == "right" or side == "r":
        exo_left_or_right_sideMultiplier = 1  # spool belt/rotate CW for right exo

    sleep(1)

    pullCurrent = 1000  # magnitude only, not adjusted based on leg side yet

    desCurrent = pullCurrent * exo_left_or_right_sideMultiplier

    # fxs = flex.FlexSEA()

    # dev_id = fxs.open(port, baud_rate, debug_logging_level)
    # fxs.start_streaming(dev_id, freq=streamFreq, log_en=data_log)
    # app_type = fxs.get_app_type(dev_id)

    sleep(0.5)
    dataFileTemp = "characterizationFunctionDataTemp.csv"
    with open(dataFileTemp, "w", newline="\n") as fd:
        writer = csv.writer(fd)
        while inProcedure:
            iterations += 1
            fxu.clear_terminal()
            act_pack = fxs.read_device(dev_id)
            fxs.send_motor_command(dev_id, fxe.FX_CURRENT, desCurrent)

            current_ank_angle = (
                act_pack.ank_ang * ANK_ENC_CLICKS_TO_DEG
            )  # obtain ankle angle in deg
            current_mot_angle = (
                act_pack.mot_ang * MOT_ENC_CLICKS_TO_DEG
            )  # obtain motor angle in deg

            act_current = act_pack.mot_cur

            currentTime = time()

            # OLD way of adjusting angles that accomodated offsets. But since we don't know exactly what the standing
            # position is, it's better to just use the "raw" angles to the transmission ratio

            motorAngle_adj = exo_left_or_right_sideMultiplier * -(
                current_mot_angle - motorAngleOffset_deg
            )
            ankleAngle_adj = exo_left_or_right_sideMultiplier * (
                current_ank_angle - ankleAngleOffset_deg
            )

            motorAngleVec = np.append(motorAngleVec, motorAngle_adj)
            ankleAngleVec = np.append(ankleAngleVec, ankleAngle_adj)
            print("Motor Angle: {} deg\n".format(motorAngle_adj))
            print("Ankle Angle: {} deg\n".format(ankleAngle_adj))

            if (currentTime - startTime) > interval:
                inProcedure = False
                print("Exiting Transmission Ratio Procedure\n")
                n = 50
                for i in range(0, n):
                    fxs.send_motor_command(
                        dev_id, fxe.FX_NONE, pullCurrent * (n - i) / n
                    )
                    sleep(0.04)

            writer.writerow(
                [iterations, desCurrent, act_current, motorAngle_adj, ankleAngle_adj]
            )

    p = np.polyfit(
        ankleAngleVec, motorAngleVec, 4
    )  # fit a 4th order polynomial to the ankle and motor angles
    print(p)

    print("Exiting curve characterization procedure")
    fxs.close(dev_id)
    return p, ankleAngleVec, motorAngleVec


def returnDefaultTRCurve(side: str) -> np.array:
    """Runs default Transmission Ratio curves. Replace these when recalibrating so it can be used next time.
    args:
            side (str): 'left' or 'right'

    returns:
            p_master (np.array): coefficients of 4th order polynomial fit of the TR curve
    """
    if side == "left" or side == "l":
        p_master = np.array(
            [
                -0.0003677510803188676,
                0.017151350175251136,
                12.65984341382134,
                -15.985162890894292,
            ]
        )
    elif side == "right" or side == "r":
        p_master = np.array(
            [
                -0.0002521353898815316,
                0.014202702950459948,
                12.811603243229758,
                -10.103309193627183,
            ]
        )
    return p_master


def calibrateWrapper(
    fxs,
    dev_id,
    side: str,
    port: str,
    baud_rate: int,
    recalibrateZero: bool,
    recalibrateCurve: bool,
) -> Tuple[float, float, np.array, np.array]:
    """Calibrates the Exoskeletons and generates a transmission ratio curve using the methods above.
    args:
            fxs
            dev_id: device ID
            side (str): 'left' or 'right'
            port (str): port name
            baud_rate (int): baud rate
            recalibrateZero (bool): recalibrate zero
            recalibrateCurve (bool): recalibrate curve

    returns:
            motorAngleOffset_deg (float): motor angle offset in degrees
            ankleAngleOffset_deg (float): ankle angle offset in degrees
            charCurve_poly_fit (np.array): polynomial coefficients of the motor-angle curve
            TR_poly_fit (np.array): polynomial coefficients of the transmission ratio curve
    """

    if side == "left" or side == "l":
        filename = "offsets_ExoLeft.csv"
    elif side == "right" or side == "r":
        filename = "offsets_ExoRight.csv"

    # conduct zeroing/homing procedure and log offsets
    if recalibrateZero:
        with open(filename, "w") as file:

            print(side)
            print("Starting ankle zeroing/homing procedure...\n")
            (motorAngleOffset_deg, ankleAngleOffset_deg) = zeroProcedure(
                fxs, dev_id, side, port, baud_rate
            )
            print("succesfully obtained offsets")

            writer = csv.writer(file, delimiter=",")

            writer.writerow([motorAngleOffset_deg, ankleAngleOffset_deg])

            file.close()

    else:

        raise Exception("You must zero every time you restart the exos")

    # conduct transmission ratio curve characterization procedure and store curve
    if recalibrateCurve:
        filename2 = "char_curve_{0}_{1}.csv".format(side, strftime("%Y%m%d-%H%M%S"))
        print("Starting ankle transmission ratio procedure...\n")
        print(
            "Begin rotating the angle joint starting from extreme plantarflexion to extreme dorsiflexion...\n"
        )
        charCurve_poly_fit, ankle_angle, motor_angle = characterizeTRCurve(
            fxs,
            dev_id,
            side,
            port,
            baud_rate,
            motorAngleOffset_deg,
            ankleAngleOffset_deg,
        )
        TR_poly_fit = np.polyder(charCurve_poly_fit)  # polynomial deriv coefficients (derivative of the motor angle vs ankle angle curve yields the TR)

        # plot motor-ankle angle graph
        plt.figure(1)
        plt.plot(ankle_angle, motor_angle)
        polyfitted_motor_angle_curve = np.polyval(charCurve_poly_fit, ankle_angle)
        plt.plot(
            ankle_angle,
            polyfitted_motor_angle_curve,
            label="polyfit",
            linestyle="dashed",
        )
        plt.xlabel("ankle angle")
        plt.ylabel("motor angle")

        # plot TR curve (interpolate polyfit params incase it isn't accurate):
        plt.figure(2)
        TR_curve = np.polyval(TR_poly_fit, ankle_angle)
        plt.plot(ankle_angle, TR_curve, label="polyfit")
        pchip_TR_curve = interpolate.PchipInterpolator(ankle_angle, TR_curve)
        plt.plot(
            ankle_angle, pchip_TR_curve(ankle_angle), linewidth=5, label="pchip auto"
        )

        with open(filename2, "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(charCurve_poly_fit)
            writer.writerow(TR_poly_fit)

    else:
        charCurve_poly_fit = returnDefaultTRCurve(side)
        TR_poly_fit = np.polyder(charCurve_poly_fit)

    print("Motor angle offset")
    print(str(motorAngleOffset_deg))
    print("Ankle angle offset")
    print(str(ankleAngleOffset_deg))
    print("Char curve")
    print(str(charCurve_poly_fit))
    print("TR curve")
    print(str(TR_poly_fit))

    return motorAngleOffset_deg, ankleAngleOffset_deg, charCurve_poly_fit, TR_poly_fit


if __name__ == "__main__":

    try:  # only works for a single exo
        port_cfg_path = "/home/pi/Actuator-Package/Python/flexsea_demo/ports.yaml"
        ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

        selected_side = input(
            "Running this code can only be done for a single exo/side. Which side would you like to do? (left/right)\n"
        )

        if selected_side == "left" or selected_side == "l":
            selected_port = ports[0]
        elif selected_side == "right" or selected_side == "r":
            selected_port = ports[1]

        motorAngleOffset_deg, ankleAngleOffset_deg, charCurve_poly_fit, TR_poly_fit = (
            calibrateWrapper(
                selected_side,
                selected_port,
                baud_rate,
                recalibrateZero=True,
                recalibrateCurve=True,
            )
        )

        print(f"Motor Angle Offset: {motorAngleOffset_deg}")
        print(f"Ankle Angle Offset: {ankleAngleOffset_deg}")
        print(f"Char Curve: {charCurve_poly_fit}")
        print(f"TR Curve: {TR_poly_fit}")

    except Exception as e:
        print("broke: " + str(e))
        print(traceback.format_exc())
        pass
