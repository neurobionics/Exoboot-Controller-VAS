%% Torque JND Post-Processing Script 
% This code determines the Just Noticeable Difference Threshold of 
% preferred ankle torque and/or knee torque for an incline activity when using 
% the Dephy Ankle Exoskeletons for the 2024-25 Vickrey VAS study. 
% The psychometric method used is the Kaernbach/staircase algorithm. 

% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/JND Processor directory
% Lab drive contains the Palamedes Library within the 'VAS_Protocol_Data/JND Data/' directory.
% Nundini Rawal, Fall 2024

% ask for path to Palamedes Library
fprintf("Select Location of the Palamedes Library Folder\n");
path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
palamedes_path = uigetdir(path,'Select Location of Palamedes Library Folder');

% ask for path to JND subject file tree
fprintf("Select Location of the JND File Tree\n");
title = 'Select Location of JND File Tree (i.e. all JND subject folders should be viewable';
JND_directory_path = uigetdir(path,title);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
sub_dict_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';
[~,sub_dictionary_file_location] = uigetfile(sub_dict_path);

% ask for path to figure folder (to save generated figures to)
fprintf("Select Folder Where you'd like to Save Generated Figures\n");
fig_gen_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/';
figure_path = uigetdir(path);

% add Palamedes directory & JND directory & subject dictionary to path
addpath(genpath(palamedes_path))
addpath(genpath(JND_directory_path))
addpath(genpath(sub_dictionary_file_location))
addpath(genpath(figure_path))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [1 3];

% specify reference torques:
ref_select = [18 29];

% specify modes:
mode_select = ["ascending", "descending"];

clc

%% For Psychometric Fitting: load JND data & create struct with proportions for all subjects
% output struct: 
% StimLevels (data values for x-axis)
% NumPos (# of trials judged more forceful than reference), 
% OutofNum (total # of trials for each stimulus lvl), 
% PS (reference)
%
% NumPos, OutofNum: 1st row is for ankle exo, 2nd row is for knee exo
% PS: 1st value is ref for ankle exo, 2nd value is ref for knee exo

num_of_exo_JNDs = 1;

for sub_num = subj_num
    % combine csvs into a single csv
    xls_sheet = subject(sub_num).JND_filenames;
    exp_data_sheet = readtable(xls_sheet);
    
    for ref = ref_select

        filtered_data = exp_data_sheet(exp_data_sheet.T_ref == ref, :);

        % Extract filtered variables
        props = filtered_data.T_comp ./ filtered_data.T_ref;
        props = props(props ~=1 );  % remove '1' from props
        AvsB = [filtered_data.T_ref, filtered_data.T_comp];

        if ismember('higher', filtered_data.Properties.VariableNames)        
            responses = [filtered_data.truth, filtered_data.higher];
        elseif ismember('peak_torque_ind', filtered_data.Properties.VariableNames)
            responses = [filtered_data.truth, filtered_data.peak_torque_ind];
        end
         
        % sort data into ascending order
        [props,sorted_idxs] = sort(props,'ascend');
        responses = responses(sorted_idxs,1:2);
    
        % find the unique props
        unique_props = unique(props);
    
        % remove '1' from unique props
        unique_props = unique_props(unique_props ~= 1);
    
        % identify repetitions of each proportion
        edges = [unique_props; max(unique_props)+1];
        [OutofNum,edges,repetitions] = histcounts(props,edges);   
    
        NumPos = zeros(size(unique_props,1),num_of_exo_JNDs);
    
        % compile proportion of trials where comparison identified as > reference
        for comparison = 1:size(props,1)
    
            % identify if comparison judged more forceful than reference
            if props(comparison) > 1
                whichishigher = 'comparison';
                whichishigherIDX = responses(comparison,1);
    
                if whichishigherIDX == responses(comparison,2)
                    % tally to NumPos of current torque setting
                    NumPos(repetitions(comparison),1) = NumPos(repetitions(comparison),1) + 1;
                end
    
            elseif props(comparison) < 1
                whichishigher = 'reference';
                whichishigherIDX = responses(comparison,1);
    
                if whichishigherIDX ~= responses(comparison,2)
                    % tally to NumPos of current torque setting
                    NumPos(repetitions(comparison),1) = NumPos(repetitions(comparison),1) + 1;
                end
    
            elseif props(comparison) == 1
                continue
            end
    
        end
    
        % convert proportions to Percent Changes from reference
        percent_changes = (unique_props - 1).*100; 
               
        % store NumPos and OutofNum for each subject in struct
        sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).NumPos =  NumPos';
        sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).OutofNum =  OutofNum;
        sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).PercentChanges =  percent_changes';

        % Also add in variables required for staircase evaluation for both modes
        for mode = mode_select
            % Filter table based on conditions
            mode_filtered_data = filtered_data(filtered_data.mode == mode, :);
            
            % Extract filtered variables
            comparison_torque = mode_filtered_data.T_comp;
            truth = mode_filtered_data.truth;
            step_sizes = mode_filtered_data.step_size;

            if ismember('pres', filtered_data.Properties.VariableNames)        
                pres_number = mode_filtered_data.pres;
            elseif ismember('Pres', filtered_data.Properties.VariableNames)        
                pres_number = mode_filtered_data.Pres;
            end

            if ismember('higher', filtered_data.Properties.VariableNames)        
                deemed_higher = mode_filtered_data.higher;
            elseif ismember('peak_torque_ind', filtered_data.Properties.VariableNames)
                deemed_higher = mode_filtered_data.peak_torque_ind;
            end
            
            % loop though truth and higher and determine if correct or incorrect
            correct_response = zeros(length(pres_number),1);
            for pres = 1:length(pres_number)
                if truth(pres) ~= deemed_higher(pres)
                    corr_resp_bool = false;
                else
                    corr_resp_bool = true;
                end
            
                correct_response(pres) = corr_resp_bool;
            end

            % store vars for each subject and ref in struct
            sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).("mode_"+mode).pres_number =  pres_number;
            sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).("mode_"+mode).comparison_torque =  comparison_torque;
            sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).("mode_"+mode).correct_response =  correct_response;
            sub_JND_proportion_data.("S"+sub_num).("ref_"+ref).("mode_"+mode).step_sizes =  step_sizes;
        end
    end
end

%% For Psychometric Fitting: Compute Parameter Values for each subject using Palamedes Library & Plot

close all; clc;

% Use the Logistic function
PF = @PAL_Logistic;

% Fix everything except for the slope
paramsFree = [1 1 0 0];  % 1: free parameter, 0: fixed parameter

% Defining parameter space through which to perform fminsearch for free
% parameters. Values specified are used as initial guesses 
searchGrid.alpha = 1; 
searchGrid.lambda = 0.02;                % fixed at 0.02 as in ps paper
searchGrid.gamma = searchGrid.lambda;    % fixed at lapse rate as in methods paper

options = PAL_minimize('options');
options.TolFun = 1e-05;

try
    prompt = "Plot individual figures to Debug? (y/n) \n";
    user_select = input(prompt,"s");
catch
    warning('User Selection does not match with available options');
end

fields = fieldnames(sub_JND_proportion_data);
for subs = 1:size(fields,1)
    sub_num = subj_num(subs);
    for cond = 1:num_of_exo_JNDs    % fitting for ankle & knee exo response data 
        for ref = ref_select
            
            % determine figure file name to save as
            JND_psy_fig_name = string(figure_path)+"/S10"+string(sub_num)+'_JND_PSY_'+string(ref)+'Nm.svg';
        
            NumPos = sub_JND_proportion_data.( fields{subs,1} ).("ref_"+ref).NumPos(cond,:);
            OutofNum = sub_JND_proportion_data.( fields{subs,1} ).("ref_"+ref).OutofNum(cond,:); 
            PercentChanges = sub_JND_proportion_data.( fields{subs,1} ).("ref_"+ref).PercentChanges(cond,:); 
            ProportionForcefulSub = NumPos./OutofNum;
    
            % estimate the slope of the curve & set the searching region about this value
            slope_est = 0.5;%( ProportionForcefulSub(14) - ProportionForcefulSub(8) )/( PercentChanges(14) - PercentChanges(8) );
            searchGrid.beta = logspace(0,10*abs(slope_est),1000);
    
            % Perform fits using fminsearch (unconstrained, nonlinear multivar 
            % optimizer; doesn't use gradients, but uses slack vars/simplex method
            disp('Fitting function.....');
            [paramsValues, LL, scenario, exitflag] = PAL_PFML_Fit(PercentChanges, NumPos, ...
                OutofNum, searchGrid, paramsFree, PF,'gammaEQlambda',1,'SearchOptions',options);
            
            disp('done:');
            message = sprintf('Slope estimate: %6.4f\r',paramsValues(2));
            disp(message);
    
            % apply parameters to function
            PercentTorquesFineGrain = -100:max(PercentChanges)/1000:100;
            ProportionForcefulModel = PF(paramsValues,PercentTorquesFineGrain);
    
            % identifies unique values in the evaluated logistic fit & groups duplicates
            [uniqueProportion, ~, groupIdx] = unique(ProportionForcefulModel);
            
            % Group the corresponding values in PercentTorquesFineGrain by averaging those percents
            meanPercentTorque = accumarray(groupIdx, PercentTorquesFineGrain, [], @mean);
            
            ProportionForcefulModel = uniqueProportion;
            PercentTorquesFineGrain = meanPercentTorque;
    
            % interpolate to find the comparison torque value at which the model 
            % predicts 25 & 75% of the reference were judged more forceful 
            x25 = interp1(ProportionForcefulModel, PercentTorquesFineGrain, 0.25);
            x75 = interp1(ProportionForcefulModel, PercentTorquesFineGrain, 0.75);
            JND = (x75-x25)/2;
    
            % plot the raw data with logistic fit and display JND on plot
            if user_select == "y"
                figure
                plot(PercentChanges,ProportionForcefulSub,'k.','markersize',40);
                set(gca, 'fontsize',16);
                % set(gca, 'Xtick',PercentChanges);
                axis([min(PercentChanges) max(PercentChanges) 0 1]);
                xlabel('Percent Change from Reference (%)');
                ylabel('Proportion(\psi)'); % Proportion of Trials judged higher than Reference 
                hold on
                
                plot(PercentTorquesFineGrain,ProportionForcefulModel,'-','color',[0 .7 0],'linewidth',4);
                box off
                hold on
    
                txt = {'JND = ' num2str(JND) '%'};
                text(0.9,0.9,txt,'FontSize',14)
                % Add a dynamic title
                % title(['Sub: ', num2str(subs, '%d'), ', Ref: ', num2str(ref, '%.1f')]);

                % save the current figure if it doesn't exist
                if exist(JND_psy_fig_name,'file') == 0
                    saveas(gcf,JND_psy_fig_name);
                end

            end
    
            % store paramValues and JNDs
            sub_JND_proportion_data.( fields{subs,1} ).("ref_"+ref).paramsValues(cond,:) = paramsValues;
            sub_JND_proportion_data.( fields{subs,1} ).("ref_"+ref).JND(1,cond) = JND;
        end
    end
end

%% Plot Staircase Statistics

fields = fieldnames(sub_JND_proportion_data);
for sub = 1:size(fields,1)
    sub_num = subj_num(sub);
    for cond = 1:num_of_exo_JNDs    
        for ref = ref_select
            for mode = mode_select

                % determine figure file name to save as
                JND_stair_fig_name = string(figure_path)+"/S10"+string(sub_num)+'_JND_STAIR_'+string(ref)+'Nm_'+string(mode)+'.svg';
        
                % extract data from subject JND struct
                correct_response = sub_JND_proportion_data.( fields{sub,1} ).("ref_"+ref).("mode_"+mode).correct_response(:,cond);
                T_comp = sub_JND_proportion_data.( fields{sub,1} ).("ref_"+ref).("mode_"+mode).comparison_torque(:,cond);
                pres_number = sub_JND_proportion_data.( fields{sub,1} ).("ref_"+ref).("mode_"+mode).pres_number(:,cond);
                step_sizes = sub_JND_proportion_data.( fields{sub,1} ).("ref_"+ref).("mode_"+mode).step_sizes(:,cond);
                psychometric_JND = sub_JND_proportion_data.( fields{sub,1} ).("ref_"+ref).JND;
                
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                %%% A). compute the JND using the average of reversals method: %%%
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                
                % Find reversal points
                diffs = diff(correct_response) ~= 0;
                reversal_indices = find(diff(correct_response) ~= 0); 
                
                % Extract comparison torques at reversal points
                reversal_torques = T_comp(reversal_indices);
                
                % Compute the average of the torques at reversal points
                average_reversal_torque = mean(reversal_torques);
                
                % Display the result
                fprintf('The average comparison torque at reversal points is: %.2f\n', average_reversal_torque);
                fprintf('The average of reversals resultant JND is: %.2f\n', abs(ref - average_reversal_torque))
                
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                %%% B). determine staircase stimulus progression %%%
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                
                figure;
                hold on;
                
                for i = 1:length(pres_number)
                    if correct_response(i)
                        % Filled circle for correct responses
                        plot(pres_number(i), T_comp(i), 'ko', 'MarkerFaceColor', 'k');
                    else
                        % Unfilled circle for incorrect responses
                        plot(pres_number(i), T_comp(i), 'ko');
                    end
                end
                
                % Add a horizontal line for the reference torque
                yline(ref, '--r', 'LineWidth', 1.5, 'Label','Ref torque');
                
                if (mode == "ascending")
                    % Add line from psychometric function computed JND:
                    yline(ref - psychometric_JND/100*ref, '--b', 'LineWidth', 1.5, 'Label','Psi-JND');
                else
                    % Add line from psychometric function computed JND:
                    yline(ref + psychometric_JND/100*ref, '--b', 'LineWidth', 1.5, 'Label','Psi-JND');
                end
                
                yline(average_reversal_torque,'--m', 'LineWidth', 1.5, 'Label','Avg of Reversals JND' )
                
                % Customize plot
                xlabel('Comparison Number');
                ylabel('Comparison Torque Magnitude');
                % title(['Responses for Reference Torque: ', num2str(ref)]);
                legend('Correct Response', '', '', '', 'Incorrect Response','Location', 'Best');
                
                if (mode == "ascending")
                    axis([min(pres_number) max(pres_number) min(T_comp)-1 ref+1]);
                else
                    axis([min(pres_number) max(pres_number) ref-1 max(T_comp)-1]);
                end
                
                grid on;
                hold off;

                % save the current figure if it doesn't exist
                if exist(JND_stair_fig_name,'file') == 0
                    saveas(gcf,JND_stair_fig_name);
                end
                
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                %%% B). Plot the step size over comparison number %%%
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                figure;
                hold on;
                for i = 1:length(pres_number)
                    if correct_response(i)
                        % Filled circle for correct responses
                        plot(pres_number(i), step_sizes(i), 'ko', 'MarkerFaceColor', 'k');
                    else
                        % Unfilled circle for incorrect responses
                        plot(pres_number(i), step_sizes(i), 'ko');
                    end
                end
                
                xlabel('Comparison Number');
                ylabel('Step Size to Update Next Comparison');
                % title(['Staircase Step Sizes and Responses for Reference Torque: ', num2str(ref)]);
                % axis([min(pres_number) max(pres_number) 0.5 3]);
                legend('Correct Response', '', '', '', 'Incorrect Response','Location', 'Best');
            end
        end
    end
end

