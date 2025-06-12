#Load plotting library
from rtplot import client 

# Common imports
import numpy as np

################################################
#### Testing Transmission ratio functionality: 
################################################
# side = input("Input left/right:")

# # compute the transmission ratio for the current ankle angle:
# def get_TR_for_ank_ang(curr_ank_angle):
#     N = np.polyval(p_TR, curr_ank_angle)  # Instantaneous transmission ratio
    
#     return N

# def desired_torque_2_current(desired_spline_torque):
#     N = get_TR_for_ank_ang(25.3)
#     des_current = (desired_spline_torque / 
#                         (N * 0.9 * 0.000146) * 1000)*-1  # mA
#     return des_current

# # Open and read the CSV file
# if side == "left":
#     with open('default_TR_coefs_left.csv', mode='r') as file:
#         csv_reader = csv.reader(file)
#         p_master = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
#         p_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
#         p_TR = [float(x) for x in p_TR]

# elif side == "right":
#     with open('default_TR_coefs_right.csv', mode='r') as file:
#         csv_reader = csv.reader(file)
#         p_master = next(csv_reader)  # Read the first row, which is the motor_angle_curve_coeffs
#         p_TR = next(csv_reader)      # Read the second row, which is the TR_coeffs
#         p_TR = [float(x) for x in p_TR]
        
# print('p_master:', p_master)
# print('p_TR:', p_TR)
# desired_spline_torque = 2

# des_current = desired_torque_2_current(desired_spline_torque)
# print("Desired current is:", des_current)



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