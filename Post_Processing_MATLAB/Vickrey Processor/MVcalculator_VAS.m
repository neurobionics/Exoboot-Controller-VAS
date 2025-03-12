%% 2024-25 Vickrey VAS Study - Computing Marginal Vaue EndPoints
% This code determines the Marginal Value of performing an incline activity 
% when (a) walking with the weight of an exoskeleton and (b) walking with 
% the preferred assistance of the exoskeleton. The exoskeletons used are 
% the Dephy Ankle Exoskeletons and a Research Prototype Knee Exoskeleton.
%
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/Vickrey Processor directory
% Author: Nundini Rawal
% Date: 8/4/2023

clc; close; clear;

%% Set file paths to access data

% ask for path to Vickrey subject file tree
fprintf("Select Location of the Vickrey File Tree\n");
path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
VA_directory_path = uigetdir(path);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
sub_dict_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';
[~,sub_dictionary_file_location] = uigetfile(sub_dict_path);

% ask for path to figure folder (to save generated figures to)
fprintf("Select Folder Where you'd like to Save Generated Figures\n");
fig_gen_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
figure_path = uigetdir(path);

% add Vickrey directory & subject dictionary & figure folder to path
addpath(genpath(VA_directory_path))
addpath(genpath(sub_dictionary_file_location))
addpath(genpath(figure_path))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

%% Initialize variables
count = 0;
gof_type = "r2";

default_buffer_size = zeros(length(subject_list),1);

% WNE vars
task_cost_WNE = default_buffer_size;
winRateWNE_list = default_buffer_size;
res_WNElist = default_buffer_size;
timeWalked_WNElist = default_buffer_size;
k_WNElist_1b = default_buffer_size;
b_WNElist_1b = default_buffer_size;

% EPO vars
EPO_MVs = default_buffer_size;
task_cost_EPO = default_buffer_size;
relative_task_cost_EPO = default_buffer_size;
cost_of_EPO_sys_per_hour_LIST = default_buffer_size;
winRateEPO_list = default_buffer_size;
res_EPOlist = default_buffer_size; 
timeWalked_EPOlist = default_buffer_size;
b_EPOlist = default_buffer_size; 
k_EPOlist = default_buffer_size;

% NPO vars
NPO_MVs = default_buffer_size;
task_cost_NPO = default_buffer_size;
relative_task_cost_NPO = default_buffer_size;
cost_of_NPO_sys_per_hour_LIST = default_buffer_size;
winRateNPO_list = default_buffer_size;
res_NPOlist = default_buffer_size;
timeWalked_NPOlist = default_buffer_size;
b_NPOlist = default_buffer_size; 
k_NPOlist = default_buffer_size;

%% Compute MV
for subj_num = 6:7%1:length(subject_list)
    WNE_fname = '';
    EPO_fname = '';
    NPO_fname = '';
    
    if subj_num == 4
        continue
    end

    % Determine appropriate filenames for each condition
    for file = 1:numel(subject(subj_num).MV_filenames)
        
        pat = ("WNE"|"EPO"|"NPO");  % determine and label which is WNE, EPO, NPO files
        cond = extract(subject(subj_num).MV_filenames(file), pat);

        switch cond
            case 'WNE'
                WNE_fname = subject(subj_num).MV_filenames(file); 
            case 'EPO'
                EPO_fname = subject(subj_num).MV_filenames(file);
                EPO_fig_name = string(figure_path)+"/S10"+string(subj_num)+'_Vickrey_EPO.svg';
            case 'NPO'
                NPO_fname = subject(subj_num).MV_filenames(file);
                NPO_fig_name = string(figure_path)+"/S10"+string(subj_num)+'_Vickrey_NPO.svg';
        end
    end

    % if there is a missing WNE entry, skip to next subject
    if (isempty(WNE_fname) == true)
        continue;
    else
        if (isempty(NPO_fname) == true)
            comp_names = {EPO_fname};
        elseif (isempty(EPO_fname) == true)
            comp_names = {NPO_fname};
        else
            comp_names = {EPO_fname, NPO_fname};
        end
    end

    % for each extracted filename, determine the Marginal Value (relative to the WNE condition)
    for i = 1:length(comp_names)

        fprintf("\n~~~~~Subject: %d, Trial Type: %s ~~~~~\n", subj_num, comp_names{1,i});
        
        % Pre-process the bids:
        [t_WNE_bids, t_cond_bids, winRateWNE, winRateCond, WNE_bids, cond_bids, t_walked_WNE, t_walked_cond, winIdxsWNE, winIdxsCond] = cutBids(WNE_fname, comp_names{1,i}, subj_num);
    
        if t_walked_WNE > 10 && t_walked_cond > 10 
            count = count + 1;
            
            % Compute MV:
            [b_WNE,k_WNE,b_cond,k_cond, cond_bids, WNE_bids, scaledWNE_t, scaledCond_t, beta_cond, beta_WNE] = lstsqParams(winRateWNE, winRateCond, t_WNE_bids, WNE_bids, t_cond_bids, cond_bids);
            [MV, dif, linmod_diff, r2_WNE, r2_cond, WNE_integral, cond_integral] = MVgenerator(b_WNE, k_WNE, b_cond, k_cond, gof_type, WNE_fname, WNE_bids, cond_bids, scaledCond_t, scaledWNE_t, winIdxsWNE, winIdxsCond);
            % [MV, dif, ~, r2_WNE, r2_cond, WNE_integral, cond_integral, lambda] = linExtrapMVgenerator(b_WNE,k_WNE,b_cond,k_cond,gof_type, [], WNE_bids, cond_bids, scaledCond_t, scaledWNE_t);
          
            WNE_price_per_hour = WNE_integral * 2;
            % WNE_price_per_hour = WNE_integral * lambda;
            
            % Store data:figure_path+subj_num+'_Vickrey.svg'
            pat = ("EPO"|"NPO");
            cond = extract(comp_names{1,i}, pat);
            
            % WNE variable storage needs to occur only once
            if i == 1
                task_cost_WNE(subj_num,1) = WNE_integral;
                winRateWNE_list(subj_num,1) = winRateWNE;
                res_WNElist(subj_num,1) = r2_WNE;
                timeWalked_WNElist(subj_num,1) = t_walked_WNE;
                k_WNElist_1b(subj_num,1) = k_WNE;
                b_WNElist_1b(subj_num,1) = b_WNE;
            end

            switch cond
                case 'EPO'
                    % save the current figure if it doesn't exist
                    if exist(EPO_fig_name, 'file') == 0
                        saveas(gcf,EPO_fig_name);
                    end

                    EPO_MVs(subj_num,1) = MV;
                    task_cost_EPO(subj_num,1) = cond_integral;
                    relative_task_cost_EPO(subj_num,1) = dif;

                    %%%%% PER HOUR COSTS: %%%%%
              
                    cost_of_EPO_sys = WNE_price_per_hour * MV/100;
                    fprintf("Monetary Cost of wearing powered sys per hour: $ %.2f% \n", cost_of_EPO_sys);
                    fprintf("\n");
                    fprintf("Monetary Cost of wearing powered sys relative to WNE per hour: $ %.2f% \n", dif*2);
                    % fprintf("Monetary Cost of wearing powered sys relative to WNE per hour: $ %.2f% \n", dif*lambda);

                    cost_of_EPO_sys_per_hour_LIST(subj_num,1) = cost_of_EPO_sys;

                    %%%%%%%%%%%%%%%%%%%%%%%%%%%
                     
                    winRateEPO_list(subj_num,1) = winRateCond;
                    res_EPOlist(subj_num,1) = r2_cond; 
                    timeWalked_EPOlist(subj_num,1) = t_walked_cond;
                
                    b_EPOlist(subj_num,1) = b_cond; 
                    k_EPOlist(subj_num,1) = k_cond; 


                case 'NPO'
                    % save the current figure if it doesn't exist
                    if exist(NPO_fig_name,'file') == 0
                        saveas(gcf,NPO_fig_name);
                    end

                    NPO_MVs(subj_num,1) = MV;
                    task_cost_NPO(subj_num,1) = cond_integral;
                    relative_task_cost_NPO(subj_num,1) = dif;
                    
                    %%%%% PER HOUR COSTS: %%%%%
                    
                    cost_of_NPO_sys = WNE_price_per_hour * MV/100;
                    fprintf("Monetary Cost of wearing unpowered sys per hour: $ %.2f% \n", cost_of_NPO_sys);
                    fprintf("\n");
                    fprintf("Monetary Cost of wearing unpowered sys relative to WNE per hour: $ %.2f% \n", dif*2);
                    % fprintf("Monetary Cost of wearing unpowered sys relative to WNE per hour: $ %.2f% \n", dif*lambda);

                    cost_of_NPO_sys_per_hour_LIST(subj_num,1) = cost_of_NPO_sys;
                    
                    %%%%%%%%%%%%%%%%%%%%%%%%%%%
                    
                    winRateNPO_list(subj_num,1) = winRateCond;
                    res_NPOlist(subj_num,1) = r2_cond;
                    timeWalked_NPOlist(subj_num,1) = t_walked_cond;
                    
                    b_NPOlist(subj_num,1) = b_cond;
                    k_NPOlist(subj_num,1) = k_cond;
            end
        end
    end
end


function [MV, diff, linmod_diff, r2_WNE, r2_EPO, WNE_integral, EPO_integral, lambda] = linExtrapMVgenerator(b_WNE,k_WNE,b_EPO,k_EPO, type, WNE_bidding_filenames, WNE_bids, EPO_bids, scaledEPO_t, scaledWNE_t) 
    
    % find the shorter of the 2 walk times
    [min_t, min_t_idx] = min([scaledEPO_t(end), scaledWNE_t(end)]);

    % set desired interval to this shorter endpoint
    desired_x_interval = linspace(0,min_t,1000);

    % interval multiplier
    desired_end_time = 60; % in mins
    lambda = desired_end_time/min_t;
    
    regressed_EPO = k_EPO*exp(b_EPO*desired_x_interval); 
    regressed_WNE = k_WNE*exp(b_WNE*desired_x_interval); 

    % to verify indiv plots are correct - plotting regressed & raw bids
    % figure();
    % plot(desired_x_interval, regressed_WNE,'r', scaledWNE_t, WNE_bids, '.r');
    % hold on;
    % plot(desired_x_interval, regressed_EPO,'b', scaledEPO_t, EPO_bids, '.b');
    % hold on;

    % title(sprintf('Regressed Bids Over Time: %s', fname), 'Interpreter','none');
    xlabel("time walked (min)"); ylabel("bids ($/min)");
    legend("WNE fit", "WNE data", "EPO fit", "EPO data");

    % find CPTW of EPO vs WNE
    WNE_integral = trapz(desired_x_interval, regressed_WNE); 
    EPO_integral = trapz(desired_x_interval, regressed_EPO); 
    diff = WNE_integral-EPO_integral; 
    MV = (diff/WNE_integral)*100;  % percent change of EPO from WNE
    fprintf("Percent Change from Wearing Exo: %.5f%%\n", MV);
    % fprintf("Cost per Hour($): %.5f%\n", MV/100*lambda*WNE_integral);
    % fprintf("Lambda is: %.5f%\n", lambda);
    % fprintf("min walk time is: %.5f%\n", min_t);
    fprintf("\n");

    if type == "mape"
        matched_len_EPO = k_EPO*exp( b_EPO*linspace(0,scaledEPO_t(end),length(EPO_bids)) );
        matched_len_WNE = k_WNE*exp( b_WNE*linspace(0,scaledWNE_t(end),length(WNE_bids)) );
        MAPE_EPO = mape(matched_len_EPO', EPO_bids);
        MAPE_WNE = mape(matched_len_WNE', WNE_bids);
        fprintf("MAPE of EPO: %.2f%%\n", MAPE_EPO);
        fprintf("MAPE of WNE: %.2f%%\n", MAPE_WNE);  fprintf("\n");

        r2_WNE = MAPE_WNE;
        r2_EPO = MAPE_EPO;
        linmod_diff = nan;
    elseif type == "r2"
        % finding difference in areas between linear models of WNE & EPO
        linMod_EPO = b_EPO*desired_x_interval + log(k_EPO); 
        linMod_WNE = b_WNE*desired_x_interval + log(k_WNE); 
        WNE_linintegral = trapz(desired_x_interval, linMod_WNE);
        EPO_linintegral = trapz(desired_x_interval, linMod_EPO);
        linmod_diff = WNE_linintegral-EPO_linintegral; 
        fprintf("Area diff in linear models($): %.2f%\n", linmod_diff);
        fprintf("\n");
    
        % compute r^2 between linearized model & linearized dataset -> 1-SSR/SST
        linModel_EPO = b_EPO*scaledEPO_t + log(k_EPO); 
        linModel_WNE = b_WNE*scaledWNE_t + log(k_WNE); 
    
        linData_WNE = log(WNE_bids);
        linData_WNE(linData_WNE == -Inf) = 0;
        linData_EPO = log(EPO_bids);
        linData_EPO(linData_EPO == -Inf) = 0;
    
        % compiling residuals & computing r^2
        res_WNE = linData_WNE - linModel_WNE;
        res_EPO = linData_EPO - linModel_EPO;
    
        r2_WNE = 1 - sum((linData_WNE-linModel_WNE).^2)/sum((linData_WNE-mean(linData_WNE)).^2);
        r2_EPO = 1 - sum((linData_EPO-linModel_EPO).^2)/sum((linData_EPO-mean(linData_EPO)).^2);
    
        %if r^2 is NaN, means fit is perfect-i.e subject bids stayed constant
        if isnan(r2_WNE) == true
            r2_WNE = 1;
        end
        if isnan(r2_EPO) == true
            r2_EPO = 1;
        end
    
        fprintf("R^2 for WNE fit: %.2f%\n", r2_WNE);
        fprintf("\n");
        fprintf("R^2 for EPO fit: %.2f%\n", r2_EPO);
        fprintf("\n");
    end
end
