import os
import csv
import datetime
import numpy as np
import matplotlib.pyplot as plt

from src.settings.constants import TR_COEFS_PREFIX, TR_FOLDER_PATH, TR_DATE_FORMATTER
# TODO: fix these next 3 imports:
from src.utils.filing_utils import get_logging_info
from opensourceleg.logging import Logger, LogLevel
CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )

class VariableTransmissionRatio:
    def __init__(
        self,
        side:str,
        tr_coefs_file_specific:str=None,
        coefs_prefix:str=TR_COEFS_PREFIX,
        filepath:str=TR_FOLDER_PATH,
        max_allowable_angle:int=180,
        min_allowable_angle:int=0,
        min_allowable_TR:int=10,
        granularity:int=10000
    )-> None:

        # Source file settings
        self.side = side
        self.tr_coefs_file_specific = tr_coefs_file_specific
        self.coefs_prefix = coefs_prefix
        self.filepath = filepath
        self.coefs_filename = None

        # TR profile settings
        self.max_allowable_angle = max_allowable_angle
        self.min_allowable_angle = min_allowable_angle
        self.min_allowable_TR = min_allowable_TR
        self.granularity = granularity

        # Get coefs file
        self.get_coefs_file()

        # Get coefs from file
        self.TR_coefs, self.motor_curve_coefs, self.offset = self.load_coefs()

        # Set TR profile
        self.TR_dict = self.set_TR_dict()

    def get_coefs_file(self):
        """
        Use tr_coefs_file_specific if available or
        Load in most recent TR coefs file for given side
        """
        if self.tr_coefs_file_specific:
            self.coefs_filename = self.tr_coefs_file_specific
        else:
            tr_files = []
            datestrings = []
            datetimes = []

            fullfileprefix = "{}_{}".format(self.coefs_prefix, self.side)
            for file in os.listdir(self.filepath):
                if fullfileprefix in file:
                    tr_files.append(os.path.join(self.filepath, file))
                    datestring = file.replace(fullfileprefix, "").strip("_").split(".")[0]
                    dt = datetime.datetime.strptime(datestring, TR_DATE_FORMATTER)
                    datestrings.append(datestring)
                    datetimes.append(dt)

            most_recent = datestrings[datetimes.index(max(datetimes))]
            self.coefs_filename = "{}_{}_{}.csv".format(self.coefs_prefix, self.side, most_recent)

        CONSOLE_LOGGER.info("TR {} USING: {}".format(self.side, self.coefs_filename))

    def load_coefs(self):
        """
        Load TR coefs, motor angle curve coefs, and dorsi offset from file
        File is obtained by running TR_characterization_MAIN.py
        """
        # Open and read the CSV file
        coefs_filepath = os.path.join(self.filepath, self.coefs_filename)

        with open(coefs_filepath, mode='r') as file:
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
    testgen = VariableTransmissionRatio("right")

    print("TR COEFS: {}".format(testgen.TR_coefs))
    print("OFFSET: {}".format(testgen.offset))

    angles = np.linspace(testgen.min_allowable_angle, testgen.max_allowable_angle, 10000)
    TRs = [testgen.get_TR(ang) for ang in angles]

    plt.scatter(angles, TRs)
    plt.title("MAX TR: {:0.3f}".format(max(TRs)))
    plt.xlabel("angle (deg)")
    plt.ylabel("TR")
    plt.show()
