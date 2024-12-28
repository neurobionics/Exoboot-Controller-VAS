%% 2024-25 Vickrey VAS Study - Post-Processes Exoboot Sensor Streams during JND Experiments
% This code plots 2 figures per subject. The 1st figure is for the left exo, 
% and the 2nd figure is for the right exo. 
%
% Each figure contains the following plots:
% (1) Forceplate data & Ankle angle vs Time
% (2) Forceplate data & Torque setpoint & Torque profile from current vs Time
% (3) Stride Period vs Time
% (4) Ankle angle & Transmission ratio vs Time
% (5) Case temperature vs Time
% (6) Motor Current & Ankle ankle vs Time
%
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/JND Processor directory
% Author: Nundini Rawal
% Date: 9/21/2024

clc; close; clear;

% ask for path to Vickrey subject file tree
fprintf("Select Location of the JND File Tree\n");
title = 'Select Location of the JND File Tree (i.e. all JND subject folders should be viewable';
path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
VAS_directory_path = uigetdir(path,title);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
[~,sub_dictionary_file_location] = uigetfile;

% add VAS directory & subject dictionary to path
addpath(genpath(VAS_directory_path))
addpath(genpath(sub_dictionary_file_location))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [1 2 3];

% specify left and right exo sides
sides = 2;

% define important variables:
k = 0.146;
eta = 0.9;  % efficiency of belt drive
mA_to_A = 1000;
scale_2_view_fp = 1/10;

%% For each subject, plot their left and right exo sensor data stream:
for sub = subj_num
    gse_data = readtable(subject(sub).JND_exo_sensor_filenames(3));
    Header_gse = gse_data.Properties.VariableNames';
    
    for curr_side = 1:sides
        % load file
        xls_sheet = subject(sub).JND_exo_sensor_filenames(curr_side);
        data = readtable(xls_sheet);
        Header_data = data.Properties.VariableNames';

        % determine side:
        if curr_side == 1
            fp_data = gse_data.forceplate_left;
            current_command = -data.motor_current/mA_to_A;
        else
            fp_data = gse_data.forceplate_right;
            current_command = -data.motor_current/mA_to_A;
        end

        % filter the motor currents
        filtd_current_cmd = filter_mot_current(current_command);

        figure()
        
        % ~~ (1) Forceplate data & Ankle Angle vs time ~~ %
        subplot(3,2,1)
        plot(gse_data.pitime, fp_data*scale_2_view_fp, 'DisplayName', 'Forceplate')
        hold on
        plot(data.pitime, data.ankle_angle, 'DisplayName', 'Ankle Angle','Color','k','LineWidth',1)
        xlabel('PI Time');
        legend('Interpreter', 'none')

        % ~~ (2) Torque setpoint & ankle torque vs time ~~ %
        subplot(3,2,2)
        hold on
        plot(data.pitime, data.peak_torque, 'DisplayName', 'Torque Setpoint')
        hold on

        ankle_torque_from_current = torque_computer(data.N, k, eta, filtd_current_cmd);
        plot(data.pitime, ankle_torque_from_current, 'DisplayName', 'Computed Torque')
        ylabel('Torque(Nm)');
        xlabel('Time');
        legend('Interpreter', 'none')

        % ~~ (3) Stride Period vs time ~~ %
        subplot(3,2,3)
        hold on
        plot(data.pitime, data.stride_period, 'DisplayName','Stride Period')
        ylabel('Period(s)');
        xlabel('Time');
        legend('Interpreter', 'none')


        % ~~ (4) Ankle angle & Transmission Ratio vs time  ~~ %
        subplot(3,2,4)
        hold on
        plot(data.pitime, data.N*10, 'DisplayName','N')
        hold on
        plot(data.pitime, data.ankle_angle, 'DisplayName','Ankle Angle')
        xlabel('Time');
        legend('Interpreter', 'none')


        % ~~ (5) Case Temperature & Forceplate vs time ~~ %
        subplot(3,2,5)
        hold on
        plot(gse_data.pitime, fp_data*scale_2_view_fp*1/10, 'DisplayName', 'Forceplate')
        hold on
        plot(data.pitime, data.temperature, 'DisplayName','Case Temp')
        xlabel('Time');
        legend('Interpreter', 'none')


        % ~~ (6) Motor Current & Ankle ankle ~~ %
        subplot(3,2,6)
        hold on
        plot(data.pitime, filtd_current_cmd, 'DisplayName','Motor Current')
        plot(data.pitime, data.ankle_angle, 'DisplayName', 'Ankle Angle')
        xlabel('Time');
        legend('Interpreter', 'none')
    end
end


%% Function to compute Ankle Torque from Current & N:
function ankle_torque_from_current = torque_computer(N, kt, eta, I)
    ankle_torque_from_current = I.*N*kt*eta;
end

%% Function to "filter" motor currents
function I = filter_mot_current(I)
    I( I > 30 ) = 0;
    I( I < -30 ) = 0;
end

