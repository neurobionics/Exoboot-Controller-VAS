
import numpy as np

def initialize_rt_plots()->list:
    """
    Initialize rtplot timeseries
    
    The following time series are plotted:
    - Current (A)
    - Temperature (°C)
    - Ankle Angle (°)
    - Transmission Ratio
    - Ankle Torque Setpoint (Nm)
    
    """
    
    current_plt_config = {'names' : ['Left', 'Right'],
                    'colors' : ['r','b'],
                    'line_style': ['-','-'],
                    'title' : "Exo Current (A) vs. Sample",
                    'ylabel': "Current (A)",
                    'xlabel': "timestep",
                    'line_width':[2,2],
                    'yrange': [0,30]
                    }

    temp_plt_config = {'names' : ['Left', 'Right'],
                    'colors' : ['r','b'],
                    'line_style': ['-','-'],
                    'title' : "Case Temperature (°C) vs. Sample",
                    'ylabel': "Temperature (°C)",
                    'xlabel': "timestep",
                    'line_width':[2,2],
                    'yrange': [20,60]
                    }
    
    ank_ang_plt_config = {'names' : ['Left', 'Right'],
                    'colors' : ['r','b'],
                    'line_style': ['-','-'],
                    'title' : "Ankle Angle (°) vs. Sample",
                    'ylabel': "Angle (°)",
                    'xlabel': "timestep",
                    'line_width':[2,2],
                    'yrange': [0,150]
                    }
    
    TR_plt_config = {'names' : ['Left', 'Right'],
                    'colors' : ['r','b'],
                    'line_style': ['-','-'],
                    'title' : "TR (°) vs. Sample",
                    'ylabel': "N",
                    'xlabel': "timestep",
                    'line_width':[2,2],
                    'yrange': [0,20]
                    }
    
    torque_plt_config = {'names' : ['Left', 'Right'],
                    'colors' : ['r','b'],
                    'line_style': ['-','-'],
                    'title' : "Torque (Nm) vs. Sample",
                    'ylabel': "Torque (Nm)",
                    'xlabel': "timestep",
                    'line_width':[2,2],
                    'yrange': [0,50]
                    }

    plot_config = [current_plt_config, temp_plt_config, ank_ang_plt_config, TR_plt_config, torque_plt_config]
    
    return plot_config

def update_rt_plots(exoboots)->list:
    """
    Updates the real-time plots with current values for:
    - Current (A)
    - Temperature (°C)
    - Ankle Angle (°)
    - Transmission Ratio
    - Ankle Torque Setpoint (Nm)
    The data is collected from the exoboots object and returned as a list of arrays.
    
    Args:
        exoboots: The exoboots object containing sensor data.
        
    Returns:
        plot_data_array: A list of data arrays for each plot.
    """

    # Create array (or numpy array) with data
    data_to_plt = [abs(exoboots.left.motor_current),
                   5,   # right motor current
                   exoboots.left.case_temperature, 
                   30,   # right case temperature
                   80,   # left ankle angle
                   60,   # right ankle angle
                   exoboots.left.gear_ratio,
                   10,   # right gear ratio
                   10,   # left torque command
                   20    # right torque command
                   ]
    
    return data_to_plt