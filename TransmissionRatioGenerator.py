import csv
import numpy as np


class TransmissionRatioGenerator:
    def __init__(self, coefs_filename, max_allowable_angle=180, min_allowable_angle=0, min_allowable_TR=10, granularity=10000):
        self.coefs_filename = coefs_filename
        self.max_allowable_angle = max_allowable_angle
        self.min_allowable_angle = min_allowable_angle
        self.min_allowable_TR = min_allowable_TR
        self.granularity = granularity

        # Get coefs from file
        self.TR_coefs, self.motor_curve_coefs, self.offset = self.load_coefs()

        self.TR_dict = self.set_TR_dict()

    def load_coefs(self):
        """
        Load TR coefs, motor angle curve coefs, and dorsi offset from file

        File is obtained by running TR_characterization_MAIN.py
        """
        # Open and read the CSV file

        with open(self.coefs_filename, mode='r') as file:
            csv_reader = csv.reader(file)
            coefs_ankle_vs_motor = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
            coefs_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
            max_dorsiflexed_ang = next(csv_reader)
            
            # convert to array of real numbers to allow for polyval evaluation
            TR_curve_coeffs = [float(x) for x in coefs_TR]
            motor_angle_curve_coeffs = [float(y) for y in coefs_ankle_vs_motor]
            max_dorsi_offset = float(max_dorsiflexed_ang[0])

        return TR_curve_coeffs, motor_angle_curve_coeffs, max_dorsi_offset
    
    def get_offset(self):
        return self.offset

    def index_to_angle(self, i):
        """
        Linearly transforms index in [0, granularity] to angle in [min_ang, max_ang]
        """
        return i / self.granularity * (self.max_allowable_angle - self.min_allowable_angle) + self.min_allowable_angle
    
    def angle_to_index(self, ang):
        """
        Linearly transforms angle in [min_ang, max_ang] to index in [0, granularity]
        """
        return (ang - self.min_allowable_angle) / (self.max_allowable_angle - self.min_allowable_angle) * self.granularity

    def set_TR_dict(self):
        """
        Creates dictionary mapping angles to instantaneous TR
        """
        return {i: np.polyval(self.TR_coefs, self.index_to_angle(i)) for i in range(self.granularity)}

    def get_TR(self, ang):
        """
        Returns instantaneous TR

        Cannot return TR lower than min_allowable_TR for safety reasons
        """
        N = self.TR_dict[max(min(int(self.angle_to_index(ang)), self.granularity - 1), 0)]
        return max(N, self.min_allowable_TR)


if __name__ == "__main__":
    prefix = "Transmission_Ratio_Characterization/default_TR_coefs_"
    leftgen = TransmissionRatioGenerator("{}{}.csv".format(prefix,"left"), max_allowable_angle=180, min_allowable_angle=0, min_allowable_TR=10, granularity=10000)
    rightgen = TransmissionRatioGenerator("{}{}.csv".format(prefix,"right"), max_allowable_angle=180, min_allowable_angle=0, min_allowable_TR=10, granularity=10000)

    for angle in np.linspace(-20, 200, 11):
        print("{}: {}, {}".format(angle, leftgen.get_TR(angle), rightgen.get_TR(angle)))