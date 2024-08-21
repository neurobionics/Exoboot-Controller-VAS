#Load plotting library
from rtplot import client 

# Common imports
import numpy as np
import csv
import array

######################################
#### Testing rtPlot Functionality ####
######################################

#Let's create two subplots
#First, define a dictionary of items for each plot

#First plot will have three traces: phase, phase_dot, stride_length
plot_1_config = {'names': ['Current (A) Left', 'Current (A) Right'],
            'title': "Current (A) vs. Sample",
            'ylabel': "Current (A)",
            'xlabel': 'Sample', 
            'yrange': [0, 30],
            "colors":['red','blue'],
            "line_width":[8,8]
            }
plot_2_config = {'names': ['Ankle Angle (deg) Left', 'Ankle Angle (deg) Right'],
            'title': "Ankle Angle (deg) vs. Sample",
            'ylabel': "Ankle Angle (deg)",
            'xlabel': 'Sample',
            'yrange': [-40, 30],
            "colors":['red','blue'],
            # "line_style":['-','-'],
            "line_width":[8,8]
            }

#Aggregate into list  
plot_config = [plot_1_config,plot_2_config]

#Tell the server to initialize the plot
client.initialize_plots(plot_config)

#Create plotter array with random data
for i in range(1000):
    plot_data_array = [20*np.sin(i),
                       20*np.cos(i),
                       20*np.sin(2*i),
                       20*np.cos(2*i)
                    # np.random.randn(), #phase
                    # np.random.randn(), #phase_dot
                    # np.random.randn(), #stride_length
                    # np.random.randn(), #gf1
                    #    np.random.randn(), #gf2
                    #    np.random.randn(), #gf3
                    #    np.random.randn(), #gf4
                    #    np.random.randn()  #gf5
                    ]

    #Send data to server to plot
    client.send_array(plot_data_array)