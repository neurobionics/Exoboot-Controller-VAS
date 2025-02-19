%% PILOT!!! 2024-25 Vickrey Value Landscape Study
% This code determines a participant's Value Landscape when using the Dephy 
% Ankle Exoskeletons and a Research Prototype Knee Exoskeleton.
%
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/VAS Processor directory
% Author: Nundini Rawal
% Date: 9/21/2024

clc; close; clearvars -except subject subject_list compiled_data

%% ask for path to Vickrey subject file tree

prompt = "Operating with Dropbox or Lab Drive? (db/lab): \n";
path_ans = input(prompt,"s");

if path_ans == "db"
    base_path = '/Users/nrawal/University of Michigan Dropbox/Nundini Rawal/Vickrey Auction Project/Value Landscape Study/';
else
    base_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';
end

fprintf("Select Location of the VAS File Tree\n");
title = 'Select Location of the VAS File Tree (i.e. all VAS subject folders should be viewable';
path = append(base_path,'VAS_Protocol_Data/');
VAS_directory_path = uigetdir(path,title);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
sub_dict_path = base_path;
[~,sub_dictionary_file_location] = uigetfile(sub_dict_path);

% add VAS directory & subject dictionary to path
addpath(genpath(VAS_directory_path))
addpath(genpath(sub_dictionary_file_location))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS_PILOT;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [2];

%% instantiate utils
utils = VAS_processor_utils();


%% Create a struct with compiled subject-by-subject data
compiled_data = struct();

for sub_num = subj_num
    per_sub_data_files = subject(sub_num).VAS_filenames;

    for file_idx = 1:length(per_sub_data_files)
        
        xls_sheet = per_sub_data_files(file_idx);

        if ~exist(xls_sheet, 'file')
          sprintf('Warning: file does not exist:\n%s', xls_sheet);
          continue
        end
        
        % load file
        exp_data_sheet = readtable(xls_sheet);
        sheet_rows = size(exp_data_sheet,1);

        % if session/group # doesn't exist, 
        if ~any("session" == string(exp_data_sheet.Properties.VariableNames))
            session_number = extract(extract(xls_sheet, regexpPattern("(?i)session\d+")), digitsPattern);
            group_number = extract(extract(xls_sheet, regexpPattern("(?i)group\d+")),digitsPattern);
            
            % insert session & group # as cols into table based on filename
            sesh_col = repelem(str2num(session_number),sheet_rows)';
            group_col = repelem(str2num(group_number),sheet_rows)';
            exp_data_sheet = addvars(exp_data_sheet,sesh_col,group_col,'NewVariableNames',{'session','group'});
        end

        % delete any cols that have trial naming
        if any("trial" == string(exp_data_sheet.Properties.VariableNames))
            exp_data_sheet.trial = [];
        end

        % set Table Headers
        exp_data_sheet = utils.set_Header(exp_data_sheet);

        % extract unique btn options in that particular file
        btn_num_types = unique(exp_data_sheet.btn_option);

        % loop through those unique buttons & fill struct
        for btn_num = 1:length(btn_num_types)
            
            % extract data from main table depending on btn option
            split_exp_data_sheet = rmmissing( exp_data_sheet(exp_data_sheet.btn_option == btn_num_types(btn_num),:), 2);
               
            % extract btn option descriptors
            group_num = split_exp_data_sheet.group;
            pres_num = split_exp_data_sheet.pres;
            max_group_num = length(unique(group_num));
            max_pres_num = max(pres_num);
            total_options = max_pres_num*btn_num_types(btn_num);
    
            torques = table2array(split_exp_data_sheet(:, contains(split_exp_data_sheet.Properties.VariableNames, 'torque')));
            values = table2array(split_exp_data_sheet(:, contains(split_exp_data_sheet.Properties.VariableNames, 'mv')));
    
            if (size(torques,2) ~= max_group_num)
                % reshape/compile torques & values into columns for each group
                % i.e. each column is a distinct group, with presentations in
                % order (every 4 OR 10 torque values is a new presentation)
                reshaped_torques = reshape(torques', total_options, max_group_num);
                reshaped_values = reshape(values', total_options, max_group_num);
            else
                reshaped_torques = torques;
                reshaped_values = values;
            end
    
            % create fieldnames dynamically for struct
            btn_num_type_field = "VAS_filename_" + btn_num_types(btn_num) + "BTN";
            subject_field = "S10" + sub_num;
            
            % if subject field doesn't exist, initialize empty struct
            if ~isfield(compiled_data, subject_field)
                compiled_data.(subject_field) = struct();
            end

            % If btn_num_type_field exists, append new data
            if isfield(compiled_data.(subject_field), btn_num_type_field)

                compiled_data.(subject_field).(btn_num_type_field).reshaped_torques = ...
                    [compiled_data.(subject_field).(btn_num_type_field).reshaped_torques, reshaped_torques];
            
                compiled_data.(subject_field).(btn_num_type_field).reshaped_values = ...
                    [compiled_data.(subject_field).(btn_num_type_field).reshaped_values, reshaped_values];

                compiled_data.(subject_field).(btn_num_type_field).max_group_num = ...
                    compiled_data.(subject_field).(btn_num_type_field).max_group_num + max_group_num;
            
            else
                % First-time assignment
                compiled_data.(subject_field).(btn_num_type_field) = struct('reshaped_torques', reshaped_torques, ...
                                                                            'reshaped_values', reshaped_values, ...
                                                                            'total_options', total_options, ...
                                                                            'max_group_num', max_group_num);
            end
        end
    end
end

%% Plot Raw Data for either all button types for each subject
subj_num = [2];
colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
group_markers = {"o", 'square', '^',};

% obtain user inputs for flexible data visualization
list = {'1BTN','4BTN','10BTN'};
[btn_select_indxs, answer_norm, btn_field_func_map] = utils.get_user_input(list);

for sub_num = subj_num
    figure
    for btn_idx = 1:length(btn_select_indxs)

        curr_btn_opt_idx = btn_select_indxs(btn_idx);
        curr_btn_opt = list(curr_btn_opt_idx);

        % If current btn idx is in map, extract {field,fcn} pair & unpackage struct vars
        [reshaped_torques, reshaped_values, total_options, ...
                max_group_num] = utils.unpack_field_func_pair(compiled_data,sub_num,btn_field_func_map,curr_btn_opt_idx);
    
        % normalize data
        if answer_norm == "y"
            torques = utils.normalize_data(reshaped_torques);
            values = utils.normalize_data(reshaped_values);
        else
            torques = reshaped_torques;
            values = reshaped_values;
        end    
    
        % plot raw data
        for i = 1:max_group_num
            scatter(torques(:,i),values(:,i), 60,...
                        "filled",...
                        "Marker",group_markers{btn_idx},...
                        'MarkerFaceColor',colors{i}, ...
                        'MarkerEdgeColor',colors{i},...
                        'MarkerFaceAlpha',0.6,...
                        'MarkerEdgeAlpha',0.6);

            % dynamic legend labelling
            base_legend_namimg = curr_btn_opt + ", " + append('group ',string(i));
            sequential_lgnd_idx = (btn_idx - 1)*max_group_num + i;
            lgnd{sequential_lgnd_idx} = base_legend_namimg;
           
            hold on
        end
    end

    title(['Subject: ',append('S10',num2str(sub_num))])  
    legend(lgnd)
    
    if answer_norm == "y"
        xlabel("Normalized Torque")
        ylabel("Normalized $/Hour")
    else
        xlabel("Normalized Torque")
        ylabel("$/Hour")
    end
end

%% Plot Each 4-button Trial and Averaged Trajectory for Selected Subjects
subj_num = [2];
avg_traj_4btn_y = zeros(20,length(subj_num));

prompt = "Operate with Normalized Data? (y/n): \n";
answer_norm = input(prompt,"s");

prompt_gof = "Plot GOF Figures? (y/n): \n";
answer_gof = input(prompt_gof,"s");

for sub_num = subj_num

    % unpackage struct vars
    if isfield(compiled_data.("S10" + sub_num), 'VAS_filename_4BTN')
        [reshaped_torques, reshaped_values, total_options, ...
                max_group_num] = utils.unpack_4BTN(compiled_data, sub_num);
    else
        continue
    end

    % normalize data
    if answer_norm == "y"
        torques = utils.normalize_data(reshaped_torques);
        values = utils.normalize_data(reshaped_values);
    else
        torques = reshaped_torques;
        values = reshaped_values;
    end
       
    % sort torque cols into ascending order & apply sort filter to values
    [sorted_torques,sort_idxs] = sort(torques);
    sorted_values = [];
    for i = 1:size(values,2)
        sorted_values(:,i) = values(sort_idxs(:,i),i);
    end

    % find average $-values
    avg_vals = mean(sorted_values(1:total_options,:),2);
    std_vals = std(sorted_values(1:total_options,:),0,2);

    % Fit best-fit curve
    x_avg = sorted_torques(:,1);
    [curve_fit,gof,output] = fit(x_avg,avg_vals,'poly4','normalize','on');

    % store for each subject
    avg_traj_4btn_y(:,sub_num) = avg_vals;

    % Compute shading bounds
    upper_bound_4btn = avg_vals + std_vals;
    lower_bound_4btn = avg_vals - std_vals;

    % plot raw data & interpolated points
    figure()
    colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
    xq = linspace(0,1,1000);
    for trial = 1:max_group_num
        x = sorted_torques(1:total_options,trial);
        v = sorted_values(1:total_options,trial);
        plot(x,v,'o','color',colors{trial});
        hold on

        vq = interp1(x,v,xq);
        plot(xq,vq,'--','color',colors{trial});
        hold on
    end

    % Add shaded region
    fill([x; flipud(x)], [upper_bound_4btn; flipud(lower_bound_4btn)], 'r', 'FaceAlpha', 0.1, 'EdgeColor', 'none');
    
    % plot avg points & trajectory
    cfit = plot(curve_fit);
    set(cfit,'color','k','LineWidth',2)
    hold on
    plot(x_avg,avg_vals,'.k','MarkerSize', 20);
    % errorbar(sorted_torques(:,1),avg_vals,std_vals,'.k','MarkerSize', 20);

    if (sub_num == 1) || (sub_num == 2)
        legend({'trial 1';'';'trial 2';'';'trial 3';'';'trial 4';'';'std'; 'curve fit thru trial avgs'});
    elseif (sub_num == 3)
        legend({'trial 1';'';'trial 2';'';'trial 3';'';'trial 4';'';'trial 5';'';'std'; 'curve fit thru trial avgs'});
    else
        legend({'trial 1';'trial 2';'trial 3';'trial 4';'trial 5'; 'trial 6'; 'std'; 'curve fit thru trial avgs'});
    end
    
    xlabel("Normalized Torque")
    ylabel("Normalized $/Hour")

    if answer_gof == "y"
        % evaluate GOF using residuals of fittype
        figure()
        subplot(2,1,1)
        plot(curve_fit,x_avg,avg_vals,"residuals")
        xlabel("Normalized Torque")
        ylabel("Residuals")
    
        subplot(2,1,2)
        residuals = output.residuals;
        plot(avg_vals,residuals,".")
        xlabel("$/Hour")
        ylabel("Residuals")
    
        % To ID Max Postiive Change in Value over Normalized Torque
        figure()
        diff_traj = diff(avg_vals);
        plot(x_avg, [0; diff_traj], "ob")
        xlabel("Normalized Torque")
        ylabel("Delta ($/Hour)")
    end

    % save the current figure if it doesn't exist
    VAS_fig_name = string(figure_path)+"/S10"+string(sub_num)+'_VAS_4BTN.svg';

    if exist(VAS_fig_name,'file') == 0
        saveas(gcf,VAS_fig_name);
    end
    
end

%% Plot 10-button Trajectories for Selected Subjects

% specify subj numbers (remove subjects due to any criteria)
subj_num = [2];
avg_traj_10btn_y = zeros(10,length(subj_num));
prompt = "Operate with Normalized Data? (y/n): \n";
answer_norm = input(prompt,"s");

for sub_num = subj_num

    % unpackage struct vars
    if isfield(compiled_data.("S10" + sub_num), 'VAS_filename_10BTN')
        [reshaped_torques, reshaped_values, total_options, ...
            max_group_num] = utils.unpack_10BTN(compiled_data, sub_num);
    else
        continue
    end

    % normalize data
    if answer_norm == "y"
        torques = utils.normalize_data(reshaped_torques);
        values = utils.normalize_data(reshaped_values);
    else
        torques = reshaped_torques;
        values = reshaped_values;
    end 

    % sort torque cols into ascending order & apply sort filter to values
    [sorted_torques,sort_idxs] = sort(torques);
    sorted_values = [];
    for i = 1:size(values,2)
        sorted_values(:,i) = values(sort_idxs(:,i),i);
    end

    % find average $-values
    avg_vals = mean(sorted_values(1:total_options,:),2);
    std_vals = std(sorted_values(1:total_options,:),0,2);

    % Compute shading bounds
    upper_bound_10btn = avg_vals + std_vals;
    lower_bound_10btn = avg_vals - std_vals;

    % store for each subject
    avg_traj_10btn_y(:,sub_num) = avg_vals;

    % Fit best-fit curve
    x = sorted_torques(:,1);
    curve_fit = fit(x,avg_vals,'poly4','normalize','on');

    % plot data
    figure()
    colors = {'b', 'r', 'g'};
    for trial = 1:max_group_num
        plot(sorted_torques(1:total_options,trial),sorted_values(1:total_options,trial),'.','MarkerSize',20, 'color',colors{trial});
        hold on
    end
    
    % plot avg points & trajectory
    cfit = plot(curve_fit);
    set(cfit,'color','k','LineWidth',2)
    errorbar(sorted_torques(:,1),avg_vals,std_vals,'.k','MarkerSize', 20);

    if sub_num == 2
        legend({'trial 1';'curve fit'; 'trial averages with std'});
    elseif sub_num == 3
        legend({'trial 1';'trial 2'; 'curve fit'; 'trial averages with std'});
    end
    xlabel("Normalized Torque")
    ylabel("Normalized $/Hour")
    
end

%% Plot 10-button Average Trajectories all together for selected subjects
subj_num = [2 3];

figure()
colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
for sub_num = subj_num
    y10 = avg_traj_10btn_y(:,sub_num);

    % Fit best-fit curve
    plot(x,y10,'.','color',colors{sub_num}, 'MarkerSize',20);
    hold on

    curve_fit = fit(x,y10,'poly4','normalize','on');
    cfit = plot(curve_fit);
    set(cfit,'color',colors{sub_num},'LineWidth',2)
    hold on
    
end
xlabel("Normalized Torque")
ylabel("Normalized $/Hour")
legend('S102 Data', 'S102 Curve Fit','S103 Data', 'S103 Curve Fit')
% title('Ten Button GUI: Average Value Trajectories Across Subjects');

%% Overlayed 4 btn with 10-button average trajectories

subj_num = [2];

figure()
colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
for sub_num = subj_num
    y4 = avg_traj_4btn_y(:,sub_num);    
    [curve_fit,gof,output] = fit(x_avg,y4,'poly4','normalize','on');    
    cfit = plot(curve_fit);
    set(cfit,'color',colors{sub_num},'LineWidth',2, 'Linestyle','--')
    hold on

    y10 = avg_traj_10btn_y(:,sub_num);
    [curve_fit,gof,output] = fit(x,y10,'poly4','normalize','on');    
    cfit = plot(curve_fit);
    set(cfit,'color',colors{sub_num},'LineWidth',2)
    hold on

end
xlabel("Normalized Torque")
ylabel("Normalized $/Hour")
legend('S102 4btn','S102 10btn', 'S103 4btn', 'S103 10btn')

