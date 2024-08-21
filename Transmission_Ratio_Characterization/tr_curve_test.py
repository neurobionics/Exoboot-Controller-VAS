# Script to visualize the Transmission Ratio Curve Output (data from TR_characterization_test.py)
# Script should be run from local machine, not the rpi to visualize the data output
#
# Author: John Hutchinson

import csv
import numpy as np
import matplotlib.pyplot as plt

motor_angles = []
ankle_angles  = []

with open("default_TR_fulldata_right.csv", newline='') as file:
    reader = csv.reader(file, delimiter=',')
    # reader.__next__()
    
    for row in reader:
        motor_angles.append(float(row[3]))
        ankle_angles.append(float(row[4]))
        
ankle_raw = np.array(ankle_angles)
motor_angles = np.array(motor_angles)

coefs = np.polyfit(ankle_raw, motor_angles, 3)

motor_raw_poly = np.polyval(coefs, ankle_raw)

deriv = np.polyder(coefs)

plt.scatter(ankle_raw, motor_angles, label='raw_data')
plt.scatter(ankle_raw, motor_raw_poly, label='polyfit')

plt.show()

print(coefs)
print(deriv)

TR_curve = np.polyval(deriv, ankle_raw)

print(max(TR_curve))

plt.scatter(ankle_raw, TR_curve)
plt.show()