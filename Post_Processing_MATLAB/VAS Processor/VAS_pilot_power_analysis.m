%% VAS Protocol Power Analysis
% General Test: Paired, two-tailed t-test; desired power is 80%; desired 
% significance level (alpha) is 5%
%
% Reminder of the Purpose of VAS Landscape Protocol: Determine the number
% of trials required per participant that reduces variability and mitigates
% the effect of the surrounding torque options.
%
% Author: Nundini Rawal (adapted from Emily Bywater's script)
% Date: 1/15/25

%=============================================%
%=========== Power Analysis Sim #1 ===========%
%=============================================%
% Purpose: Test whether torque-value relation (slope) remains significant
% across trials (i.e. signficantly different from slope = 0 across trials).

clc; clear; close all

%% ask user what their sample size and desired trial number range is:
prompt = {'Select Sim 1/2 (1/2):',...
          'Enter hypothesized number of subjects (n):',... 
          'Enter hypothesized range of trials (j_start-j_end)'};

dlgtitle = 'VAS Protocol Power Analysis Inputs';
fieldsize = [1 45; 1 45; 1 45];
default_input = {'1','10','4-10'};
answer = inputdlg(prompt,dlgtitle,fieldsize,default_input);

% use inputs to set vars:
sim_selected = str2num(answer{1});
n = str2num(answer{2});
j_range = str2num(regexprep(answer{3}, '-', ':')); % Range of trials to test

if sim_selected == 1
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Sim using linear fits through data %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Params based on normalized pilot data (self computed)
    intercept = 1.698652e-01;   % Intercept/avg user value at torque=0 
    std_intercept = 0.1803;     % avg within-sub std of intercept at torque=0 
    fixed_slope = 5.747798e-01; % Expected effect size (global slope)
    std_across_subjects = 4.562449e-01;   % Variability in slope across subjects (sample std)
    std_within_subjects = 2.783030e-01;   % Variability in slope within subjects (trial-to-trial)
    std_measurement_error = 2.783030e-01; % Avg subject-specific noise in value ratings
end

torques_per_trial = 20; 
queried_torques = sort([0.652625, 0.3921, 0.91315, 1, 0.5658, 0.175, ...
                   0.869725, 0.218425, 0.826325, 0.435525, 0.6092, ...
                   0.739475, 0.7829, 0.69605, 0.47895, 0.305275, ...
                   0.522375, 0.26185, 0.956575, 0.348675])';

num_iterations = 2000;  % Monte Carlo iterations
alpha = 0.05;           % significance level/allowable type 1 error
target_power = 0.80;    % 80% power threshold

%% begin monte carlo simulation

for j = j_range
    success = 0;
    
    for i = 1:num_iterations
        % generate sub-specific random slopes (random effect)
        subject_slopes = normrnd(fixed_slope, std_across_subjects, [n, 1]);
        
        % Initialize data storage
        torque_values = [];
        user_values = [];
        subject_ids = [];
        trial_ids = [];

        % simulate data
        for sub = 1:n
            for trial = 1:j
                
                trial_slope_variation = normrnd(0, std_within_subjects, [1, 1]); % trial-specific slope deviation
                error_within = normrnd(0, std_measurement_error, [torques_per_trial, 1]);    % observation-level noise
                
                % intercept is a random effect
                varied_intercept = normrnd(intercept, std_intercept, [1, 1]);
                
                % linear Eqn to determine user value:
                rand_torque_idxs = randperm(torques_per_trial)'; % randomized permutations of queried torques
                torques = queried_torques(rand_torque_idxs,:);
                values = varied_intercept + (subject_slopes(sub) .* torques) + (trial_slope_variation .* torques) + error_within;
                
                % store data
                torque_values = [torque_values; torques];
                user_values = [user_values; values];
                subject_ids = [subject_ids; repmat(sub, torques_per_trial, 1)];
                trial_ids = [trial_ids; repmat(trial, torques_per_trial, 1)];
            end
        end
        
        % create table of all simulated subjects data
        data = table(subject_ids, trial_ids, torque_values, user_values, ...
                     'VariableNames', {'Subject', 'Trial', 'Torque', 'Value'});
        
        % LMEM with sub-specific random slopes
        lme = fitlme(data, 'Value ~ Torque + (Torque|Subject)', 'FitMethod','REML'); 
        unbiased_output = anova(lme,'DFMethod','satterthwaite');

        % extract p-value for the slope effect (only for torque-value relation)
        pValue = unbiased_output.pValue(2);
        
        if pValue < alpha
            success = success + 1;
        end
    end
    
    % For each trial (j), compute the power
    power = success / num_iterations;
    fprintf('Trials: %d, Power: %.3f\n', j, power);
    
    % stop iterating when power reaches 80%
    if power >= target_power
        fprintf('Minimum trials required for 80%% power: %d\n', j);
        break;
    end
end





