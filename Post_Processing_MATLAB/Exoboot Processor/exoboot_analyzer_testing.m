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
% REMEMBER: exo coordinate system is y-up, x-front, z-out
% REMEMBER: bertec/vicon coordinate system is z-up, y-front, x-out
% 
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/Exoboot Processor directory
% Author: Nundini Rawal
% Date: 2/10/2025

clc; close; clearvars -except subject subject_list

%% Set Exoboot Params

% specify left and right exo sides
sides = 2;

% define important variables:
kt = 0.146;
eta = 0.9;  % efficiency of belt drive
mA_to_A = 1000;
scale_2_view_fp = 1/10;

%% Load in the exoboot_compiled_data struct from it's .mat file
if exist('VAS_exoboot_data.mat', 'file') ~= 0
    exoboot_data = load("VAS_exoboot_data.mat");
else
    unzip('zipped_VAS_exoboot_data.zip')
end

subj_num = [5];

%% Add relevant paths:
addpath(genpath('exoboot_analyzer_utils/'));

%% Parse data into % Gait Cycle and add to exoboot_data struct

for sub_num = subj_num
    subject_field = "S10" + sub_num;
    struct_base_path = exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );  % determine fields 

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        gname = detected_fields{group};
        
        fp_left = struct_base_path.(gname).GSE.forceplate_left;
        fp_right = struct_base_path.(gname).GSE.forceplate_right;
        pitime = struct_base_path.(gname).GSE.pitime;

        % Determine stance phases (1 = stance, 0 = swing)
        stance_left = fp_left >= 40;
        stance_right = fp_right >= 40;

        % Detect Heel Strikes (HS) and Toe Offs (TO)
        HS_left = find(diff(stance_left) == 1) + 1;  % Swing → Stance transition
        TO_left = find(diff(stance_left) == -1) + 1; % Stance → Swing transition
        HS_right = find(diff(stance_right) == 1) + 1;
        TO_right = find(diff(stance_right) == -1) + 1;

        % Determine the corresponding pitimes using TO and HS idxs
        pitime_HS_left = pitime(HS_left);
        pitime_TO_left = pitime(TO_left);
        pitime_HS_right = pitime(HS_right);
        pitime_TO_right = pitime(TO_right);

        % Segment strides
        num_strides = min(length(HS_left), length(HS_right)); % Ensure matching strides
        strides = struct();

        for i = 1:num_strides - 1

            % find the closest pitimes in the exothread files
            % [~,idxMatch] = find(a==interp1(a,a,29,'next'),1);

            % TODO: ID the leading foot
            leading_leg = min(HS_left(i,1), HS_right(i,1));
            
            if leading_leg == 1
                % Define stride start & end
                stride_start = HS_left(i);
                stride_end = HS_left(i+1); % Next HS defines stride end
            else
                % Define stride start & end
                stride_start = HS_right(i);
                stride_end = HS_right(i+1); % Next HS defines stride end
            end
                        
            % Extract force data for this stride
            stride_time = time(stride_start:stride_end) - time(stride_start); % Normalize time
            stride_fp_left = fp_left(stride_start:stride_end);
            stride_fp_right = fp_right(stride_start:stride_end);

            % Normalize stride to 100 points for visualization
            norm_time = linspace(0, 100, length(stride_time)); % Percentage gait cycle
            norm_fp_left = interp1(stride_time, stride_fp_left, linspace(0, stride_time(end), 100));
            norm_fp_right = interp1(stride_time, stride_fp_right, linspace(0, stride_time(end), 100));

            % Store in structure
            strides(i).time = norm_time;
            strides(i).fp_left = norm_fp_left;
            strides(i).fp_right = norm_fp_right;
        end

        % Visualization
        figure;
        hold on;
        for i = 1:length(strides)
            plot(strides(i).time, strides(i).fp_left, 'b', 'LineWidth', 1);  % Blue for left foot
            plot(strides(i).time, strides(i).fp_right, 'r', 'LineWidth', 1); % Red for right foot
        end
        xlabel('% Gait Cycle');
        ylabel('Force (N)');
        title('Force Plate Data Over Multiple Strides');
        legend('Left Foot', 'Right Foot');
        hold off;

    end
end

%% Parse data into % Gait Cycle and add to exoboot_data struct -- REDO

colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
leg_identifiers = {'left', 'right'};

for sub_num = subj_num

    subject_field = "S10" + sub_num;
    struct_base_path = exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        gname = detected_fields{group};
        per_group_data = struct_base_path.(gname);
   
        for leg_i = 1:numel(leg_identifiers)
            leg = leg_identifiers{leg_i};

            % extract relevant data
            [fp, gse_time, ank_ang, accel_y, peak_torque, mot_curr, N, ...
                exo_time,thread_freq, stride_period] = extract_data_per_leg(leg,per_group_data);

            % compute torque using torque model
            calculated_torque = torque_calculator(mot_curr, N, kt);

            % ignore everything until the first peak torque cmd > 0 arrives
            start_event_ID_idx = find(peak_torque > 0,1);

            % align GSE & exothread segments
            cut_fp = fp(1:length(exo_time));
            cut_fp(1:start_event_ID_idx-1) = 0;
            cut_gse_time = gse_time(1:length(exo_time));

            % Identify points above the threshold
            above_thresh = cut_fp >= 40;
            
            % Find rising edges (crossing above threshold)
            gait_event_idxs = find(diff([0; above_thresh]) == 1);
            event_times = exo_time(gait_event_idxs);

            % compute derivative of accely using avg exothread logging period
            % avg_thread_freq = mean(thread_freq);
            % ddx_accel_y = ddt(accel_y,1/avg_thread_freq);
    
            % filtd_ddx_accel_y = exoboot_data_filterer(ddx_accel_y,thread_freq,140,0e4);
    
            % begin ID'ing TO & HS events based on stride period and max filtered ddx_accel_y
            
    
            % sample the stride period
            avg_stride_period = mean(stride_period);
            avg_samples_in_stride = avg_thread_freq*avg_stride_period;
            window_size = avg_samples_in_stride;
    
            figure; hold on;
            % findpeaks(cut_filtd_ddx_accel_y,1:length(cut_filtd_ddx_accel_y),'MinPeakDistance',avg_samples_in_stride)
           
            % plot time series data in same figure with different colors for each group
            plot(gse_time - gse_time(1),fp*scale_2_view_fp,'Color',colors{group},'LineWidth',1.5);
            hold on
            plot(cut_gse_time - cut_gse_time(1),cut_fp*scale_2_view_fp,'-c','LineWidth',1.5);
            hold on
            plot(exo_time - exo_time(1), ank_ang,'-r','LineWidth',1.5);
            hold on
            plot(exo_time - exo_time(1), accel_y,'-k','LineWidth',1.5);
            hold on
            plot(exo_time - exo_time(1), peak_torque,'-g','LineWidth',1.5);
            hold on
            plot(exo_time - exo_time(1),calculated_torque,'--g','LineWidth',1.5);
            hold on
            xline(event_times,'-');
            grid on    
            
    
            ylim([0 100]);
            xlabel('pitime');
            ylabel('Data');
            
            if group == 1
                legend('forceplate','ank ang');
            end

        end
     
    end
        
end

%% (2) Torque setpoint & Torque profile from current vs Time
colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};

for sub_num = subj_num

    subject_field = "S10" + sub_num;
    struct_base_path = exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );  % determine fields 

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        figure;
        [t,s] = title(['Subject: ',append('S10',num2str(sub_num))],'Torque Setpoint vs. Current-Calculated Torque','Color','k');
        t.FontSize = 16;
        s.FontAngle = 'italic';

        gname = "group" + group;

        curr_Amp_left = abs(struct_base_path.(gname).left.motor_current/mA_to_A);
        N_left = struct_base_path.(gname).left.N;
        exo_time_left = struct_base_path.(gname).left.pitime;

        curr_Amp_right = abs(struct_base_path.(gname).right.motor_current/mA_to_A);
        N_right = struct_base_path.(gname).right.N;
        exo_time_right = struct_base_path.(gname).right.pitime;

        torque_setpt_left = struct_base_path.(gname).left.torque_command;
        torque_setpt_right = struct_base_path.(gname).right.torque_command;
        calculated_torque = kt*curr_Amp_left.*N_left;
        calculated_torque_right = kt*curr_Amp_right.*N_right;

        % plot time series data in same figure with different colors for each group
        % plot()
        % hold on

        plot(exo_time_left,torque_setpt_left,'-r','LineWidth',2);
        hold on
        plot(exo_time_right,torque_setpt_right,'-g','LineWidth',2);
        hold on
        plot(exo_time_left,calculated_torque,'--r','LineWidth',1);
        hold on
        plot(exo_time_right,calculated_torque_right,'--g','LineWidth',1);
        grid on    

       

        ylim([0 40]);
        xlabel('pitime');
        ylabel('Torque (Nm)');
    end
        
end

%% (2.1) For each torque setpt, compile corresponding 

%% (3) Stride Period vs Time

%% (4) Ankle angle & Transmission ratio vs Time

%% (5) Case temperature vs Time

%% (6) Motor Current & Ankle ankle vs Time

%% (7) Ensure Symmetry in Functionality between both sides