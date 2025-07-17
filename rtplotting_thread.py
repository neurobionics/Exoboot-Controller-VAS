import threading
from typing import Type

from rtplot import client
from base_exo_thread import BaseThread
from src.utils.SoftRTloop import FlexibleSleeper
from src.settings.constants import *


class rtPlottingThread(BaseThread):
    """
    Thread to continuously plot data from the left and right device threads.
    This thread subscribes to the left and right device threads and plots the data in real-time
    using the rtplot client.
    It uses a FlexibleSleeper to manage the timing of the plotting updates.
    """

    def __init__(
        self,
        thread_left,
        thread_right,
        name="rtplot",
        daemon=True,
        quit_event=Type[threading.Event],
        pause_event=Type[threading.Event],
        log_event=Type[threading.Event],
    ):
        super().__init__(name, daemon, quit_event, pause_event, log_event)
        self.device_thread_left = thread_left
        self.device_thread_right = thread_right

    def initialize_rt_plots(self) -> list:
        """
        Initialize plots for data streaming. The following time series are plotted:
            - Current (A)
            - Temperature (°C)
            - Ankle Angle (°)
            - Transmission Ratio (TR)
        """

        # assuming both sides are active
        active_sides_list = ["left", "right"]

        print("Active actuators:", active_sides_list)

        # pre-slice colors based on the number of active actuators
        colors = ["r", "b"][: len(active_sides_list)]
        if len(active_sides_list) > len(colors):
            raise ValueError(
                "Not enough unique colors for the number of active actuators."
            )

        # repeat line styles and widths for each active actuator
        line_styles = ["-" for _ in active_sides_list]
        line_widths = [2 for _ in active_sides_list]

        current_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Exo Current (A) vs. Sample",
            "ylabel": "Current (A)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 30],
        }

        temp_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Case Temperature (°C) vs. Sample",
            "ylabel": "Temperature (°C)",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [20, 60],
        }

        angle_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "Ankle Angle vs. Sample",
            "ylabel": "°",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 150],
        }

        TR_plt_config = {
            "names": active_sides_list,
            "colors": colors,
            "line_style": line_styles,
            "title": "TR vs. Sample",
            "ylabel": "N",
            "xlabel": "timestep",
            "line_width": line_widths,
            "yrange": [0, 20],
        }

        plot_config = [current_plt_config, temp_plt_config, angle_config, TR_plt_config]

        return plot_config

    def update_rt_plots(self) -> list:
        """
        Updates the real-time plots with current values:
                - Current (A)
                - Temperature (°C)
                - Ankle Angle
                - Transmission Ratio

            Returns:
                plot_data_array: A list of data arrays for each plot.
        """

        data_to_plt = []

        for device_thread in [self.device_thread_left, self.device_thread_right]:
            data_to_plt.extend(
                [
                    abs(
                        device_thread.data_dict["motor_current"]
                        * EB51_CONSTANTS.Kt
                        / 1000
                    ),  # Motor current
                    device_thread.data_dict["temperature"],  # Case temperature
                    device_thread.data_dict["ankle_angle"],  # Ankle angle
                    device_thread.data_dict["N"],  # Gear ratio
                ]
            )

        return data_to_plt

    def on_pre_run(self):
        """
        Runs once before starting main loop.
        Initializes the rtplot client and creates the plot layouts.
        """
        # initialize rtplot client and setup plots
        client.configure_ip(IP_ADDRESSES.RTPLOT_IP)
        plot_config = self.initialize_rt_plots()
        client.initialize_plots(plot_config)

        # instantiate soft real time loop with proper frequency
        self.softRTloop = FlexibleSleeper(period=1 / THREAD_FREQS.LOGGING_FREQ)

    def pre_iterate(self):
        """
        Runs even if threads are paused
        """
        pass

    def iterate(self):
        """
        Update rtplotter estimates.
        Does not update when threads paused.
        """
        # send data to server & update real-time plots
        data_to_plt = self.update_rt_plots()
        client.send_array(data_to_plt)

    def post_iterate(self):
        """
        Soft real time loop pause.
        """
        self.softRTloop.pause()

    def run(self):
        """
        Run method for the rtplotting thread.
        """
        self.on_pre_run()
        try:
            while self.quit_event.is_set():
                self.pre_iterate()
                if self.pause_event.is_set():
                    self.iterate()
                else:
                    pass
                self.post_iterate()
        except Exception as e:
            print("ERROR {}: {}".format(self.name, e))
        finally:
            pass
