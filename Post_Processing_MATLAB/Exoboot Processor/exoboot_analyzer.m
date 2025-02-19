%% 2024-25 Vickrey VAS Study - Determining $-Value over Time
% This code processes onboard exoboot sensor data to determine the
% performance of the mid-level torque-controller. 
%
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
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/Exoboot Processor directory
% Author: Nundini Rawal
% Date: 2/10/2025

clc; close; clearvars -except subject subject_list exoboot_compiled_data

%% Set Exoboot Params

% specify left and right exo sides
sides = 2;

% define important variables:
kt = 0.146;
eta = 0.9;  % efficiency of belt drive
mA_to_A = 1000;
scale_2_view_fp = 1/10;

%% Load in the exoboot_compiled_data struct from it's .mat file

exoboot_data = load("VAS_exoboot_data.mat");
subj_num = [5];

%% (1) Forceplate data & Ankle angle vs Time

colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};

for sub_num = subj_num
    figure; hold on;
    
    [t,s] = title(['Subject: ',append('S10',num2str(sub_num))],'Forceplate vs. Ankle Angle Plot','Color','k');
    t.FontSize = 16;
    s.FontAngle = 'italic';

    subject_field = "S10" + sub_num;
    struct_base_path = exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );  % determine fields 

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        gname = "group" + group;
        subplot(tot_groups,1,group);

        fp = struct_base_path.(gname).GSE.forceplate_left;
        gse_time = struct_base_path.(gname).GSE.pitime;

        ank_ang = struct_base_path.(gname).left.ankle_angle;
        exo_time = struct_base_path.(gname).left.pitime;

        % plot time series data in same figure with different colors for each group
        plot(gse_time,fp*scale_2_view_fp,'Color',colors{group},'LineWidth',1.5);
        hold on
        plot(exo_time,ank_ang,'--','Color',colors{group},'LineWidth',1.5);
        grid on    

        ylim([0 100]);
        xlabel('pitime');
        ylabel('Data');
        
        if group == 1
            legend('forceplate','ank ang');
        end
        
    end
        
end

%% (2) Forceplate data & Torque setpoint & Torque profile from current vs Time

%% (3) Stride Period vs Time

%% (4) Ankle angle & Transmission ratio vs Time

%% (5) Case temperature vs Time

%% (6) Motor Current & Ankle ankle vs Time

%% (7) Ensure Symmetry in Functionality between both sides