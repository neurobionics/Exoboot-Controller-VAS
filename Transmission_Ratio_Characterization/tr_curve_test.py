# Script to visualize the Transmission Ratio Curve Output (data from TR_characterization_test.py)
# Script should be run from local machine, not the rpi to visualize the data output
#
# Author: John Hutchinson

import os, sys, csv, datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splrep, splev

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from constants import *


def get_fulldata_file(side):
    """
    Load in most recent fulldata coefs file for given side
    """
    filepath = os.getcwd()
    fulldataname = TR_FULLDATA_PREFIX

    tr_files = []
    datestrings = []
    datetimes = []

    fullfileprefix = "{}_{}".format(fulldataname, side)
    for file in os.listdir(filepath):
        if fullfileprefix in file:
            tr_files.append(os.path.join(filepath, file))
            datestring = file.replace(fullfileprefix, "").strip("_").split(".")[0]
            dt = datetime.datetime.strptime(datestring, TR_DATE_FORMATTER)
            datestrings.append(datestring)
            datetimes.append(dt)

    most_recent = datestrings[datetimes.index(max(datetimes))]
    fulldata_file_newest = "{}_{}_{}.csv".format(fulldataname, side, most_recent)
    print("USING: {}".format(fulldata_file_newest))
    return fulldata_file_newest


def main(file):
    ankle_raw = []
    motor_raw = []
    with open(file, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        # reader.__next__()
        for row in reader:
            ankle_raw.append(float(row[4]))
            motor_raw.append(float(row[3]))

    # Sort by ankle angles
    ankle_sorted, p = np.unique(ankle_raw, return_index=True)
    motor_sorted = np.array(motor_raw)[p]

    # Polyfit
    coefs = np.polyfit(ankle_sorted, motor_sorted, 6)
    motor_poly = np.polyval(coefs, ankle_sorted)
    deriv_poly = np.polyder(coefs)
    TR_poly = np.polyval(deriv_poly, ankle_sorted)

    # Spline
    n_interior_knots = 6
    qs = np.linspace(0, 1, n_interior_knots+2)[1:-1]
    knots = np.quantile(ankle_sorted, qs)
    spl = splrep(ankle_sorted, motor_sorted, t=knots, k=3)
    motor_fit_spl = splev(ankle_sorted, spl)
    deriv_spl = splev(ankle_sorted, spl, der=1)


    # Plots
    plt.scatter(ankle_sorted, motor_sorted, label='RAW')
    plt.scatter(ankle_sorted, motor_poly, marker='+', label='POLYFIT')
    plt.scatter(ankle_sorted, motor_fit_spl, marker='X', label='SPLINE')
    plt.legend()
    plt.show()

    plt.scatter(ankle_sorted, TR_poly, label="TR_POLY")
    plt.scatter(ankle_sorted, deriv_spl, label="TR_SPLINE")
    plt.legend()
    plt.show()

    # Print coefs
    print(coefs)
    print(deriv_poly)
    print("MAX RATIO: {}".format(max(TR_poly)))


if __name__ == "__main__":
    _, side = sys.argv
    file = get_fulldata_file(side)
    main(file)
