function [fp, gse_time, ank_ang, ...
            accel_x, accel_y, accel_z, ...
            gyro_x, gyro_y, gyro_z, ...
            peak_torque, mot_curr, N, curr_cmd, ...
            exo_time,thread_freq, stride_period] = extract_data_per_leg(leg, datapath)
    % extract_data_per_leg
    %   Extracts the relevant gait state estimator data and exothread data
    %   for a specified leg (i.e. left or right)
    %
    %   Author: Nundini Rawal
    %   date: 3/25/2025

    mA_to_A = 1000;

    % obtain GSE data
    fp = datapath.GSE.( strcat("forceplate_",leg) );
    gse_time = datapath.GSE.pitime;

    % obtain exothread data
    ank_ang = datapath.(leg).ankle_angle;

    gyro_x = datapath.(leg).gyro_x;
    gyro_y = datapath.(leg).gyro_y;
    gyro_z = datapath.(leg).gyro_z;
    
    accel_x = datapath.(leg).accel_x;
    accel_y = datapath.(leg).accel_y;
    accel_z = datapath.(leg).accel_z;

    curr_cmd = datapath.(leg).current_command;
    mot_curr = abs(datapath.(leg).motor_current/mA_to_A);
    N = datapath.(leg).N;
    peak_torque = datapath.(leg).peak_torque;

    thread_freq = datapath.(leg).thread_freq;
    stride_period = datapath.(leg).stride_period;
    exo_time = datapath.(leg).pitime;
    
end