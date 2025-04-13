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
scale_2_view_accel = 10;

%% Select subject(s)

subj_num = [5];

%% Load in the exoboot_compiled_data struct from it's .mat file

for sub_num = subj_num
    mat_name = "S10" + sub_num + "_VAS_exoboot_data.mat";
    zip_name = "S10" + sub_num + "_zipped_VAS_exoboot_data.zip";
    
    if exist(mat_name, 'file') ~= 0
        raw_exoboot_data = load(mat_name);
    else
        unzip(zip_name)
        raw_exoboot_data = load(mat_name);
    end
end

%% Add relevant paths:
addpath(genpath('exoboot_analyzer_utils/'));

%% Visualize raw timeseries data from GSE and Exothread files

colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
leg_identifiers = {'left', 'right'};

prompt = "Plot left & right leg data in same figure? (y/n): \n";
leg_ans = input(prompt,"s");

for sub_num = subj_num

    subject_field = "S10" + sub_num;
    struct_base_path = raw_exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        gname = detected_fields{group};
        per_group_data = struct_base_path.(gname);
   
        if leg_ans == "y"
            figure; hold on;
        end

        for leg_i = 1:numel(leg_identifiers)
            leg = leg_identifiers{leg_i};

            % extract relevant data
            [fp, gse_time, ank_ang, accel_x, accel_y, accel_z, ...
                gyro_x, gyro_y, gyro_z, peak_torque, mot_curr, N, curr_cmd, ...
                exo_time, thread_freq, stride_period] = extract_data_per_leg(leg,per_group_data);

            % compute torque using torque model
            calculated_torque = torque_calculator(mot_curr, N, kt);

            % Synchronization (Interpolate force plate data to match IMU timestamps)
            fp_interp = interp1(gse_time, fp, exo_time, 'linear', 'extrap');

                                % START SECTION
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            % ID Heel-strike and Toe-off events
            fp_threshold = 20; 
            [HS_idx, TO_idx] = detect_gait_events(fp_interp, fp_threshold);

            % ignore everything until the first peak torque cmd > 0 arrives
            start_event_ID_idx = find(peak_torque > 0,1);

            % truncate HS & TO idx events to be after assistance start
            HS_idx = HS_idx(HS_idx > start_event_ID_idx);

            % ensure there exists HS and TO events
            if length(HS_idx) < 2 || isempty(TO_idx)
                warning('Not enough heel strikes or toe-offs detected for valid gait cycles.');
                continue;
            end

             % Compute % gait cycle for each HS-HS segment & find mapping to N
             [N_rep_curve, percent_gc] = percent_gait_AND_N_mapper(HS_idx, N, exo_time);

             % Compute theoretical torque
             theoretical_torque = kt*curr_cmd/mA_to_A.*N_rep_curve;

            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                % END SECTION





                                % START SECTION
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            % data_cut_idxs = find(round(exo_time,2) == 1007.11);
            % data_cut_idx = data_cut_idxs(2);
            % 
            % 
            % new_exo_time = exo_time(data_cut_idx:end);
            % new_theoretical_torque = theoretical_torque(data_cut_idx:end);
            % new_peak_torque = peak_torque(data_cut_idx:end);
            % 
            % % find the avg peak torque for each peak torque setpt
            % torque_list = [10.47, 20.89, 7.0, 13.94, 17.42, 24.36, 34.78, ...
            %     38.26, 27.84, 31.31, -87.12];
            % for torque_setpt = torque_list
            %     setpt_idxs = find(round(new_peak_torque,2) == torque_setpt);
            % 
            %     setpt_start = setpt_idxs(1);
            %     setpt_end = setpt_idxs(end);
            %     setpt_theoretical_torques = new_theoretical_torque(setpt_start:setpt_end);
            %     setpt_cut_exo_time = new_exo_time(setpt_start:setpt_end);
            % 
            %     % remove irrelevant peak idxs:
            %     % removal_idxs = find(round(new_peak_torque,2) == torque_setpt);
            %     % IDd_peak_torque_idxs(IDd_peak_torque_idxs == ) = [];
            % 
            %     IDd_peak_torque_idxs = findpeaks(setpt_theoretical_torques,setpt_cut_exo_time,'MinPeakDistance',1.2);
            %     findpeaks(setpt_theoretical_torques,setpt_cut_exo_time,'MinPeakDistance',1.2);
            % 
            % end

            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                % END SECTION

            if leg_ans == "y"
                plot(exo_time, fp_interp*scale_2_view_fp,'-','Color',colors{leg_i},'LineWidth',1.5); hold on
                plot(exo_time, ank_ang,':','Color',colors{leg_i},'LineWidth',1.5); hold on
                plot(exo_time, peak_torque,'*','Color',colors{leg_i},'LineWidth',1.5); hold on
                plot(exo_time, calculated_torque,'--','Color',colors{leg_i},'LineWidth',1.5); hold on
                plot(exo_time, N,'-.','Color',colors{leg_i},'LineWidth',1.5); hold on
               
                grid on   
                xlabel('pitime');
                ylabel('Data');
                legend('GRF','ank ang','peak torque setpt','calculated torque','N');
            else
                % ank angle data
                figure; hold on;
                plot(gse_time, fp*scale_2_view_fp,'-b','LineWidth',1.5); hold on
                % plot(exo_time, fp_interp*scale_2_view_fp,'--b','LineWidth',1.5); hold on
                plot(exo_time, ank_ang,'-r','LineWidth',1.5); hold on
                plot(exo_time, peak_torque,'-g','LineWidth',1.5); hold on
                plot(exo_time, calculated_torque,'--g','LineWidth',1.5); hold on
                plot(exo_time, N,'--k','LineWidth',1.5); hold on
                % plot(exo_time, curr_cmd/mA_to_A,'-c','LineWidth',1.5); hold on
                % plot(exo_time, percent_gc*50,'-m','LineWidth',1.5); hold on
                % plot(exo_time, N_rep_curve,'-.k','LineWidth',1.5); hold on
                grid on   
                xlabel('pitime');
                ylabel('° Data');
                legend('forceplate','ank ang','peak torque setpt','calculated torque','N');
                % legend('forceplate','ank ang','peak torque setpt','calculated torque','N', 'exo current cmd', 'percent GC','representative N');

                                % START SECTION                
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                % % theoretical torque 
                % figure; hold on;
                % plot(gse_time, fp*scale_2_view_fp,'-b','LineWidth',1.5); hold on
                % plot(exo_time, ank_ang,'-r','LineWidth',1.5); hold on
                % plot(exo_time, N,'--k','LineWidth',1.5); hold on
                % plot(exo_time, N_rep_curve,'-.k','LineWidth',1.5); hold on
                % 
                % plot(exo_time, peak_torque,'-g','LineWidth',1.5); hold on
                % plot(exo_time, calculated_torque,'--g','LineWidth',1.5); hold on
                % plot(exo_time, theoretical_torque,'-.b','LineWidth',1.5); hold on
                % plot(exo_time, curr_cmd/mA_to_A,'-c','LineWidth',1.5); hold on
                % plot(exo_time, percent_gc*50,'-m','LineWidth',1.5); hold on
                % 
                % grid on   
                % xlabel('pitime');
                % ylabel('Data');
                % legend('forceplate','ank ang','N','represenative N',...
                %     'peak torque setpt','calculated torque',...
                %     'theoretical torque', 'exo current cmd', 'percent GC');
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                 % END SECTION

                % gyro data
                figure; hold on;
                plot(gse_time, fp*scale_2_view_fp,'-b','LineWidth',1.5); hold on
                plot(exo_time, gyro_x,'-r','LineWidth',1.5); hold on
                plot(exo_time, gyro_y,'-k','LineWidth',1.5); hold on
                plot(exo_time, gyro_z,'-c','LineWidth',1.5); hold on
                plot(exo_time, peak_torque,'-g','LineWidth',1.5); hold on
                plot(exo_time, calculated_torque,'--g','LineWidth',1.5); hold on
                grid on   
                xlabel('pitime');
                ylabel('gyro data');
                legend('forceplate','gyrox','gyroy','gyroz','peak torque setpt','calculated torque');

                   
                % accelerometer data
                figure; hold on;
                plot(gse_time, fp*scale_2_view_fp,'-b','LineWidth',1.5); hold on
                plot(exo_time, ank_ang,'-r','LineWidth',1.5); hold on
                plot(exo_time, accel_x*scale_2_view_accel,'-r','LineWidth',1.5); hold on
                plot(exo_time, accel_y*scale_2_view_accel,'-k','LineWidth',1.5); hold on
                plot(exo_time, accel_z*scale_2_view_accel,'-c','LineWidth',1.5); hold on
                plot(exo_time, peak_torque,'-g','LineWidth',1.5); hold on
                plot(exo_time, calculated_torque,'--g','LineWidth',1.5); hold on
                grid on    
                xlabel('pitime');
                ylabel('accelerometer data');
                legend('forceplate','accelx','accely','accelz','peak torque setpt','calculated torque');

            end
        end
    end  
end
%% Segment data into gait cycles 
leg_identifiers = {'left', 'right'};

for sub_num = subj_num

    subject_field = "S10" + sub_num;
    struct_base_path = raw_exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );

    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
        gname = detected_fields{group};
        per_group_data = struct_base_path.(gname);
   
        for leg_i = 1:numel(leg_identifiers)
            leg = leg_identifiers{leg_i};

            % extract relevant data
            [fp, gse_time, ank_ang, accel_x, accel_y, accel_z, ...
                gyro_x, gyro_y, gyro_z, peak_torque, mot_curr, N, ...
                exo_unix_time, thread_freq, stride_period] = extract_data_per_leg(leg,per_group_data);

            avg_exo_freq = mean(thread_freq);
            avg_stride_period = mean(stride_period);
            if leg_i == 1
                min_stride_period = min(stride_period);
                max_stride_period = max(stride_period);
            end
            exo_time = exo_unix_time - exo_unix_time(1);

            % compute torque using torque model
            calculated_torque = torque_calculator(mot_curr, N, kt);

            % synchronize fp data to match exo timestamps
            fp_interp = interp1(gse_time, fp, exo_time, 'linear', 'extrap');

            % ID Heel-strike and Toe-off events
            fp_threshold = 20; 
            [HS_idx, TO_idx] = detect_gait_events(fp_interp, fp_threshold);

            % ignore everything until the first peak torque cmd > 0 arrives
            start_event_ID_idx = find(peak_torque > 0,1);

            % truncate HS & TO idx events to be after assistance start
            HS_idx = HS_idx(HS_idx > start_event_ID_idx);
            
            % ensure there exists HS and TO events
            if length(HS_idx) < 2 || isempty(TO_idx)
                warning('Not enough heel strikes or toe-offs detected for valid gait cycles.');
                continue;
            end

           % Visualization
            figure; hold on;
            plot(exo_time, fp_interp, '-b', 'DisplayName', 'Force Plate Data'); hold on
            plot(exo_time(HS_idx), fp_interp(HS_idx), 'go', 'DisplayName', 'Heel Strike'); hold on
            plot(exo_time(TO_idx), fp_interp(TO_idx), 'ro', 'DisplayName', 'Toe Off'); hold on
            plot(exo_time, ank_ang, 'k', 'DisplayName', 'ankle angles'); hold on
            legend();
            
            % segment into gait cycles and store in struct
            per_gait_cycle = gait_cycle_segmenter(HS_idx, ...
                min_stride_period, max_stride_period, fp_interp, ank_ang, ...
                accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, peak_torque, ...
                mot_curr, N, exo_time, TO_idx, calculated_torque);

            % create a new struct that contains gait cycle segmented data
            leg_field = "percent_GC_"+leg;
            gc_segmented_exoboot_data.(subject_field).(gname).(leg_field) = per_gait_cycle;
        end
    end  
end

%% For each peak torque set point, plot calculated torque and std vs % gait cycle - fig per leg

leg_identifiers = {'left', 'right'};

% for each subject
for sub_num = subj_num
    % access subject specific data
    subject_field = "S10" + sub_num;
    struct_base_path = gc_segmented_exoboot_data.(subject_field);
    detected_fields = fieldnames( struct_base_path );

    % for each group
    tot_groups = size(detected_fields,1);
    for group = 1:tot_groups
    
        % access group specific data
        gname = detected_fields{group};
        per_group_data = struct_base_path.(gname);
        
        % for each leg
        for leg_i = 1:numel(leg_identifiers)
            leg = leg_identifiers{leg_i};

            figure;
            subplott = tiledlayout('flow', 'TileSpacing', 'compact', 'Padding', 'compact');

            % access leg specific data from gc_segmented_exoboot_data
            leg_field = "percent_GC_"+leg;
            per_gait_cycle = gc_segmented_exoboot_data.(subject_field).(gname).(leg_field);

            % extract the peak torque variable
            peak_torques_cell_array = per_gait_cycle.peak_torque;

            % ID peak torque setpoints for each gait cycle
            pk_torque_per_GC_list = cellfun(@unique,peak_torques_cell_array,'UniformOutput',false);
            
            % ID and remove 2x1 double cells (transitional torques)
            remove_torque_transitions = cellfun(@(cell_i) isequal(size(cell_i), [2, 1]), pk_torque_per_GC_list);

            % set those transitions to empty
            pk_torque_per_GC_list(remove_torque_transitions) = {[]};

            % ID all unique peak torque setpoints
            unique_pk_torque_list = unique(cell2mat(pk_torque_per_GC_list));

            % if 0 Nm is part of the unique pk torque list, remove it
            unique_pk_torque_list(unique_pk_torque_list == 0) = [];

            % create dictionary mapping unique peak torques to the cells containing them
            torque_dict = dictionary();
            stride_count_per_torque_opt = zeros(length(unique_pk_torque_list),1);
            for i = 1:length(unique_pk_torque_list)
                pk_torque = unique_pk_torque_list(i);

                % find cells containing this specific torque
                mapped_cells = find(cellfun(@(x) any(x == pk_torque), pk_torque_per_GC_list));
                stride_count_per_torque_opt(i) = length(mapped_cells);
                torque_dict(pk_torque) = {mapped_cells};
            end
                       
            % for each unique peak torque
            for pk_torque_i = 1:length(unique_pk_torque_list)
                pk_torque = unique_pk_torque_list(pk_torque_i);
                extracted_cells = torque_dict(pk_torque);
                mapped_cells = extracted_cells{1};        
                
                % add a subplot for that particular peak torque
                nexttile
                
                % for each cell/gait cycle in the dictionary
                for sel_cell_i = 1:length(mapped_cells)
                    sel_cell = mapped_cells(sel_cell_i);
                    % extract the exo time
                    time = per_gait_cycle.time{sel_cell,1};
                    % extract the mot current
                    mot_curr = per_gait_cycle.mot_curr{sel_cell,1};
                    % extract N
                    N = per_gait_cycle.N{sel_cell,1};

                    % compute calculated torque
                    calculated_torque = torque_calculator(mot_curr, N, kt);
                    
                    % rescale exo time to be from 0-100%
                    percent_time = (time - time(1)) / (time(end) - time(1)) * 100;

                    % plot the calculated torque vs gait cycle in the current subplot
                    hold on
                    plot(percent_time, calculated_torque);
                    hold on
                end

                title("Torque Setpoint: " + pk_torque + "Nm")
                ylim([0 pk_torque + 2]);
                hold on

            end

            title(subplott, ['Peak Torque Profiles for ', leg, ' leg'])
            xlabel(subplott,'Gait Cycle (%)')
            ylabel(subplott,'Torque (Nm)')
        end
    end
end

