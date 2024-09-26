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

% ask for path to Vickrey subject file tree
fprintf("Select Location of the Vickrey File Tree\n");
title = 'Select Location of the Vickrey File Tree (i.e. all Vickrey subject folders should be viewable';
path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
VA_directory_path = uigetdir(path,title);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
[~,sub_dictionary_file_location] = uigetfile;

% add Vickrey directory & subject dictionary to path
addpath(genpath(VA_directory_path))
addpath(genpath(sub_dictionary_file_location))

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
for subj_num = 1:length(subject_list)
    WNE_fname = '';
    EPO_fname = '';
    NPO_fname = '';

    % Determine appropriate filenames for each condition
    for file = 1:numel(subject(subj_num).MVfilenames)
        
        pat = ("WNE"|"EPO"|"NPO");  % determine and label which is WNE, EPO, NPO files
        cond = extract(subject(subj_num).MVfilenames(file), pat);

        switch cond
            case 'WNE'
                WNE_fname = subject(subj_num).MVfilenames(file); 
            case 'EPO'
                EPO_fname = subject(subj_num).MVfilenames(file);
            case 'NPO'
                NPO_fname = subject(subj_num).MVfilenames(file);
        end
    end

    % if there is a missing WNE entry, skip to next subject
    if (isempty(WNE_fname) == true)
        continue;
    else
        if (isempty(NPO_fname)== true)
            comp_names = {EPO_fname};
        elseif (isempty(EPO_fname)== true)
            comp_names = {NPO_fname};
        else
            comp_names = {EPO_fname, NPO_fname};
        end
    end

    % for each extracted filename, determine the Marginal Value 
    % (relative to the WNE condition)
    for i = 1:length(comp_names)
        
        % Pre-process the bids:
        [t_WNE_bids, t_cond_bids, winRateWNE, winRateCond, WNE_bids, cond_bids, t_walked_WNE, t_walked_cond] = cutBids(WNE_fname, comp_names{1,i});
    
        if t_walked_WNE > 10 && t_walked_cond > 10 
            count = count + 1;
            
            % Compute MV:
            [b_WNE,k_WNE,b_cond,k_cond, cond_bids, WNE_bids, scaledWNE_t, scaledCond_t, beta_cond, beta_WNE] = lstsqParams(winRateWNE, winRateCond, t_WNE_bids, WNE_bids, t_cond_bids, cond_bids);
            [MV, diff, linmod_diff, r2_WNE, r2_cond, WNE_integral, cond_integral] = MVgenerator(b_WNE,k_WNE,b_cond,k_cond, gof_type, WNE_fname, WNE_bids, cond_bids, scaledCond_t, scaledWNE_t);
            WNE_price_per_hour = WNE_integral * 2;
            
            % Store data:
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
                    EPO_MVs(subj_num,1) = MV;
                    task_cost_EPO(subj_num,1) = cond_integral;
                    relative_task_cost_EPO(subj_num,1) = diff;

                    %%%%% PER HOUR COSTS: %%%%%
              
                    cost_of_EPO_sys = WNE_price_per_hour * MV/100;
                    fprintf("Monetary Cost of wearing powered sys per hour: $ %.2f% \n", cost_of_EPO_sys);
                    fprintf("\n");
                    fprintf("Monetary Cost of wearing powered sys relative to WNE per hour: $ %.2f% \n", diff*2);

                    cost_of_EPO_sys_per_hour_LIST(subj_num,1) = cost_of_EPO_sys;

                    %%%%%%%%%%%%%%%%%%%%%%%%%%%
                     
                    winRateEPO_list(subj_num,1) = winRateCond;
                    res_EPOlist(subj_num,1) = r2_cond; 
                    timeWalked_EPOlist(subj_num,1) = t_walked_cond;
                
                    b_EPOlist(subj_num,1) = b_cond; 
                    k_EPOlist(subj_num,1) = k_cond; 


                case 'NPO'
                    NPO_MVs(subj_num,1) = MV;
                    task_cost_NPO(subj_num,1) = cond_integral;
                    relative_task_cost_NPO(subj_num,1) = diff;
                    
                    %%%%% PER HOUR COSTS: %%%%%
                    
                    cost_of_NPO_sys = WNE_price_per_hour * MV/100;
                    fprintf("Monetary Cost of wearing unpowered sys per hour: $ %.2f% \n", cost_of_NPO_sys);
                    fprintf("\n");
                    fprintf("Monetary Cost of wearing unpowered sys relative to WNE per hour: $ %.2f% \n", diff*2);

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