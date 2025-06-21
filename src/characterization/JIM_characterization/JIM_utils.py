import time
from opensourceleg.logging import Logger, LogLevel

class JIM_data_plotter:
    def __init__(self, actuators: dict) -> None:
        """
        Initialize the JIM data plotter with a dictionary of actuators.

        Args:
            actuators (dict): A dictionary where keys are actuator tags and values are actuator objects.
        """
        self.actuators = actuators

    def initialize_JIM_rt_plots(self) -> list:
        """
        Initialize plots for JIM data streaming. The following time series are plotted:
            - Current (A)
            - Temperature (°C)
            - Ankle Angle (°)
            - Transmission Ratio (TR)
        """

        # converting actuator dictionary keys to a list
        active_sides_list = list(self.actuators.keys())

        print("Active actuators:", active_sides_list)

        # pre-slice colors based on the number of active actuators
        colors = ['r', 'b'][:len(active_sides_list)]
        if len(active_sides_list) > len(colors):
            raise ValueError("Not enough unique colors for the number of active actuators.")

        # repeat line styles and widths for each active actuator
        line_styles = ['-' for _ in active_sides_list]
        line_widths = [2 for _ in active_sides_list]

        current_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Exo Current (A) vs. Sample",
                        'ylabel': "Current (A)",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,30]
                        }

        temp_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Case Temperature (°C) vs. Sample",
                        'ylabel': "Temperature (°C)",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [20,60]
                        }

        angle_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "Ankle Angle vs. Sample",
                        'ylabel': "°",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,150]
                        }

        TR_plt_config = {'names' : active_sides_list,
                        'colors' : colors,
                        'line_style': line_styles,
                        'title' : "TR vs. Sample",
                        'ylabel': "N",
                        'xlabel': "timestep",
                        'line_width': line_widths,
                        'yrange': [0,20]
                        }

        plot_config = [current_plt_config, temp_plt_config, angle_config, TR_plt_config]

        return plot_config

    def update_JIM_rt_plots(self) -> list:
        """
        Updates the real-time plots with current values while JIM testing:
                - Current (A)
                - Temperature (°C)
                - Ankle Angle
                - Transmission Ratio

            The data is collected from the exoboots object and returned as a list of arrays.
            This is done for each active actuator only.

            Returns:
                plot_data_array: A list of data arrays (for active actuators) for each plot.
        """

        data_to_plt = []

        for actuator in self.actuators.values():
            data_to_plt.extend([
                abs(actuator.motor_current),   # Motor current
                actuator.case_temperature,     # Case temperature
                actuator.ankle_angle,          # Ankle angle
                actuator.gear_ratio,           # Gear ratio
            ])

        return data_to_plt

    def track_variables_for_JIM_logging(self, logger: Logger) -> None:
        """
        Track variables for each active actuator for logging to a single file
        time, N, motor current, ankle angle, temperature
        """

        for actuator in self.actuators.values():
            logger.track_variable(lambda: time.time(), f"pitime")
            logger.track_variable(lambda: actuator.gear_ratio, f"{actuator._tag}_TR")
            logger.track_variable(lambda: actuator.motor_current, f"{actuator._tag}_current_mA")
            logger.track_variable(lambda: actuator.ankle_angle, f"{actuator._tag}_ankang_deg")
            logger.track_variable(lambda: actuator.case_temperature, f"{actuator._tag}_case_temp_C")

            tracked_vars = logger.get_tracked_variables()
            print("Tracked variables:", tracked_vars)


# TODO: COMPLETE THIS FUNCTION
def JIM_time_position_vec_generator(start_velocity:float, final_velocity:float, target_position:float, total_time: float)->None:
    """
    This method reports a time and position vector for use during JIM testing.

    Args:
        - start_velocity: starting speed of JIM in dps
        - final_velocity: final speed of the JIM to hit in dps
        - target_position: final position of JIM (to accelerate to) in °
        - total_time: total time of JIM test in seconds

    Returns:
        - time_vec: vector of times
        - position_vec: vector of positions
    """

    return time_vec, position_vec


if __name__ == "__main__":

    logger = Logger(log_path='JIM_vec_test/',
                    file_name='JIM_vec_test',
                    buffer_size=1000,
                    file_level = LogLevel.DEBUG,
                    stream_level = LogLevel.INFO,
                    enable_csv_logging = True
                )

    start_dps = input("start speed in dps: ")
    end_dps = input("end speed in dps: ")
    pos = input("deg to accelerate to: ")
    total_time = input("desired end time for JIM test: ")

    time_vec, position_vec = JIM_time_position_vec_generator(start_dps, end_dps, pos, total_time)
