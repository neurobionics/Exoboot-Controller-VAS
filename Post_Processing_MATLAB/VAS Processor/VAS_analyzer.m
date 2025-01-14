%% 2024-25 Vickrey VAS Study - Determining Value Landscape
% This code determines a participant's Value Landscape when using the Dephy 
% Ankle Exoskeletons and a Research Prototype Knee Exoskeleton.
%
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/VAS Processor directory
% Author: Nundini Rawal
% Date: 9/21/2024

clc; close; clear;

% ask for path to Vickrey subject file tree
fprintf("Select Location of the VAS File Tree\n");
title = 'Select Location of the VAS File Tree (i.e. all VAS subject folders should be viewable';
path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
VAS_directory_path = uigetdir(path,title);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
sub_dict_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';
[~,sub_dictionary_file_location] = uigetfile(sub_dict_path);

% ask for path to figure folder (to save generated figures to)
fprintf("Select Folder Where you'd like to Save Generated Figures\n");
fig_gen_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
figure_path = uigetdir(path);

% add VAS directory & subject dictionary to path
addpath(genpath(VAS_directory_path))
addpath(genpath(sub_dictionary_file_location))
addpath(genpath(figure_path))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [1 2 3];

%% Plot Each Trial and Averaged Trajectory for Selected Subjects
subj_num = [1 2 3];
avg_traj_4btn_y = zeros(20,length(subj_num));

for sub_num = subj_num

    % load file
    xls_sheet = subject(sub_num).VAS_filename_4BTN;
    exp_data_sheet = readmatrix(xls_sheet);
    
    % extract data
    rows_2_extract = 1:size(exp_data_sheet(1:end,1));
   
    btn_num = exp_data_sheet(rows_2_extract,1);
    trial_num = exp_data_sheet(rows_2_extract,2);
    pres_num = exp_data_sheet(rows_2_extract,3);
    torques = exp_data_sheet(rows_2_extract,4:2:10);   
    values = exp_data_sheet(rows_2_extract,[5 7 9 11]);
    max_trial_num = max(trial_num);
    max_pres_num = max(pres_num);
    total_options = max_pres_num*btn_num(1);

    % compile into columns for each trial
    reshaped_torques = reshape(torques', total_options, max_trial_num);
    reshaped_values = reshape(values', total_options, max_trial_num);

    % normalize data
    normd_torques = reshaped_torques/max(reshaped_torques,[],"all");
    normd_values = reshaped_values/max(abs(reshaped_values),[],"all");
   
    % sort torque cols into ascending order & apply sort filter to values
    [sorted_torques,sort_idxs] = sort(normd_torques);
    sorted_values = normd_values(sort_idxs,:);

    % find average $-values
    avg_vals = mean(sorted_values(1:total_options,:),2);
    std_vals = std(sorted_values(1:total_options,:),0,2);

    % Fit best-fit curve
    x_avg = sorted_torques(:,1);
    [curve_fit,gof,output] = fit(x_avg,avg_vals,'poly1','normalize','on');

    % store for each subject
    avg_traj_4btn_y(:,sub_num) = avg_vals;

    % Compute shading bounds
    upper_bound = avg_vals + std_vals;
    lower_bound = avg_vals - std_vals;

    % plot raw data & interpolated points
    figure()
    colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
    xq = linspace(0,1,1000);
    for trial = 1:max_trial_num
        x = sorted_torques(1:total_options,trial);
        v = sorted_values(1:total_options,trial);
        plot(x,v,'o','color',colors{trial});
        hold on

        vq = interp1(x,v,xq);
        plot(xq,vq,'--','color',colors{trial});
        hold on
    end

    % Add shaded region
    fill([x; flipud(x)], [upper_bound; flipud(lower_bound)], 'r', 'FaceAlpha', 0.1, 'EdgeColor', 'none');
    
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

    % TODO: 


    % TODO: introduce better fitting methods that weigh points using noise


    % save the current figure if it doesn't exist
    % VAS_fig_name = string(figure_path)+"/S10"+string(sub_num)+'_VAS_4BTN.svg';
    % 
    % if exist(VAS_fig_name,'file') == 0
    %     saveas(gcf,VAS_fig_name);
    % end
    
end

%% Plot 4-button Average Trajectories all together for selected subjects
subj_num = [1 2 3];

figure()
colors = {"#0072BD", "#D95319", "#EDB120", "#A2142F", "#7E2F8E", "#4DBEEE"};
for sub_num = subj_num
    y = avg_traj_4btn_y(:,sub_num);
    plot(x_avg,y,'color',colors{sub_num}, 'LineWidth',2);
    hold on
end
xlabel("Normalized Torque")
ylabel("Normalized $/Hour")
legend('S101', 'S102', 'S103')
title('Four Button GUI: Average Value Trajectories Across Subjects');


%% Plot 10-button Trajectories for Selected Subjects

% specify subj numbers (remove subjects due to any criteria)
subj_num = [2 3];
avg_traj_10btn_y = zeros(10,length(subj_num));

for sub_num = subj_num

    % load file
    xls_sheet = subject(sub_num).VAS_filename_10BTN;
    exp_data_sheet = readmatrix(xls_sheet);

    rows_2_extract = 1:size(exp_data_sheet(1:end,1));
    
    % extract data
    btn_num = exp_data_sheet(rows_2_extract,1);
    trial_num = exp_data_sheet(rows_2_extract,2);
    pres_num = exp_data_sheet(rows_2_extract,3);
    torques = exp_data_sheet(rows_2_extract,4:2:23);
    values = exp_data_sheet(rows_2_extract,5:2:23);
    max_trial_num = max(trial_num);
    max_pres_num = max(pres_num);
    total_options = max_pres_num*btn_num(1);

    % compile into columns for each trial
    reshaped_torques = reshape(torques', total_options, max_trial_num);
    reshaped_values = reshape(values', total_options, max_trial_num);

    % normalize data
    normd_torques = reshaped_torques/max(reshaped_torques,[],"all");
    normd_values = reshaped_values/max(abs(reshaped_values),[],"all");
   
    % sort torque cols into ascending order & apply sort filter to values
    [sorted_torques,sort_idxs] = sort(normd_torques);
    sorted_values = normd_values(sort_idxs,:);

    % find average $-values
    avg_vals = mean(sorted_values(1:total_options,:),2);
    std_vals = std(sorted_values(1:total_options,:),0,2);

    % store for each subject
    avg_traj_10btn_y(:,sub_num) = avg_vals;

    % Fit best-fit curve
    x = sorted_torques(:,1);
    curve_fit = fit(x,avg_vals,'poly4','normalize','on');

    % plot data
    figure()
    colors = {'b', 'r', 'g'};
    for trial = 1:max_trial_num
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
    y = avg_traj_10btn_y(:,sub_num);

    % Fit best-fit curve
    plot(x,y,'.','color',colors{sub_num}, 'MarkerSize',20);
    hold on

    curve_fit = fit(x,y,'poly4','normalize','on');
    cfit = plot(curve_fit);
    set(cfit,'color','k','LineWidth',2)
    hold on
    
end
xlabel("Normalized Torque")
ylabel("Normalized $/Hour")
legend('S102 Data', 'S102 Curve Fit','S103 Data', 'S103 Curve Fit')
title('Ten Button GUI: Average Value Trajectories Across Subjects');

   






