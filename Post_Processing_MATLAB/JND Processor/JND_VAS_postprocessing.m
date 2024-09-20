% This code determines the Just Noticeable Difference Threshold of 
% preferred ankle torque and knee torque for an incline activity when using 
% the Dephy Ankle Exoskeletons and a Research Prototype Knee Exoskeleton.
% for the 2024-25 Vickrey VAS study. 

% Should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/JND Processor directory
% Lab drive contains the Palamedes Library.
% Nundini Rawal, Fall 2024

% add Palamedes folder & subdirectories to path
addpath(genpath('/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/JND Pilot/Palamedes'))
addpath(genpath('/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis'))

% loading in subject info from dictionary
[subject, subject_list] = TESTING_sub_dict_VAS;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [4];

%% load JND data & create struct with proportions for all subjects
% output struct: 
% StimLevels (data values for x-axis)
% NumPos (# of trials judged more forceful than reference), 
% OutofNum (total # of trials for each stimulus lvl), 
% PS (reference)
%
% NumPos, OutofNum: 1st row is for ankle exo, 2nd row is for knee exo
% PS: 1st value is ref for ankle exo, 2nd value is ref for knee exo

num_of_exo_JNDs = 1;
tol = 1e-2;

for sub_num = subj_num

    % combine csvs into a single csv
    xls_sheet = subject(sub_num).JNDfilenames;
    output_fname = "ALL_" + subject_list(sub_num) + "_data.csv";    % name of file containing combined data
    input_path = xls_sheet; % location of .csv files
    csv_combiner(xls_sheet, output_fname)
   
    exp_data_sheet = readmatrix(output_fname);
    
    props = exp_data_sheet(:,2);
    AvsB = exp_data_sheet(:,3:4);   % extract data
    responses = exp_data_sheet(:,5:6);

    % sort data into ascending order
    [props,sorted_idxs] = sort(props,'ascend');
    responses = responses(sorted_idxs,1:2);

    % find the unique props
    unique_props = unique(props);

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
        elseif props(comparison) < 1
            whichishigher = 'reference';
            whichishigherIDX = responses(comparison,1);
        end
        
        if whichishigherIDX == responses(comparison,2)
            % tally to NumPos of current torque setting
            NumPos(repetitions(comparison),1) = NumPos(repetitions(comparison),1) + 1;
        end

    end
           
    % store NumPos and OutofNum for each subject in struct
    sub_JND_proportion_data.( extractBetween(input_path,'Pilot/',' JND') ).NumPos =  NumPos';
    sub_JND_proportion_data.( extractBetween(input_path,'Pilot/',' JND') ).OutofNum =  OutofNum;
    sub_JND_proportion_data.( extractBetween(input_path,'Pilot/',' JND') ).Props =  unique_props';
end

%% Compute Parameter Values for each subject using Palamedes Library & Plot

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

for subs = 1:size(fieldnames(sub_JND_proportion_data),1)
    fields = fieldnames(sub_JND_proportion_data);
        
    for cond = 1:num_of_exo_JNDs    % fitting for ankle & knee exo response data 
        
        NumPos = sub_JND_proportion_data.( fields{subs,1} ).NumPos(cond,:);
        OutofNum = sub_JND_proportion_data.( fields{subs,1} ).OutofNum(cond,:); 
        Props = sub_JND_proportion_data.( fields{subs,1} ).Props(cond,:); 
        ProportionForcefulSub = NumPos./OutofNum;

        % estimate the slope of the curve & set the searching region about this value
        slope_est = ( ProportionForcefulSub(6) - ProportionForcefulSub(3) )/( Props(6) - Props(3) );
        searchGrid.beta = logspace(0,10*slope_est,1000);

        % Perform fits using fminsearch (unconstrained, nonlinear multivar 
        % optimizer; doesn't use gradients, but uses slack vars/simplex method
        disp('Fitting function.....');
        [paramsValues, LL, scenario, exitflag] = PAL_PFML_Fit(Props, NumPos, ...
            OutofNum, searchGrid, paramsFree, PF,'gammaEQlambda',1,'SearchOptions',options);
        
        disp('done:');
        message = sprintf('Slope estimate: %6.4f\r',paramsValues(2));
        disp(message);

        % apply parameters to function
        CompTorquesFineGrain = 0.3:max(Props)/1000:2;
        ProportionForcefulModel = PF(paramsValues,CompTorquesFineGrain);

        % interpolate to find the comparison stiffness value at which the model 
        % predicts 0.25 & 75% of the reference were judged stiffer 
        x25 = interp1(ProportionForcefulModel, CompTorquesFineGrain, 0.25);
        x75 = interp1(ProportionForcefulModel, CompTorquesFineGrain, 0.75);
        JND = (x75-x25)/2;

        % plot the raw data with logistic fit and display JND on plot
        if user_select == "y"
            figure
            plot(Props,ProportionForcefulSub,'k.','markersize',40);
            set(gca, 'fontsize',16);
            set(gca, 'Xtick',Props);
            axis([min(Props) max(Props) 0 1]);
            xlabel('Fraction of Preferred Stiffness');
            ylabel('\psi'); % Proportion of Trials judged Stiffer than Reference 
            hold on
            
            plot(CompTorquesFineGrain,ProportionForcefulModel,'-','color',[0 .7 0],'linewidth',4);
            
            if cond == 1
                title( sprintf('Subject %d Incline', subj_num(subs)), 'Interpreter','none' );
            elseif cond == 2
                title( sprintf('Subject %d Decline', subj_num(subs)), 'Interpreter','none' );
            end
            box off
            hold on

            txt = {'JND = ' num2str(JND)};
            text(0.9,0.9,txt,'FontSize',14)
        end

        % store paramValues and JNDs
        sub_JND_proportion_data.( fields{subs,1} ).paramsValues(cond,:) = paramsValues;
        sub_JND_proportion_data.( fields{subs,1} ).JND(1,cond) = JND;
    end
end

%% Plot Subject-Specific Ankle & Knee Exo JND Curves in Same Subplot for Each Subject
% close; clc;

figure('name','Plot Per Subject');
CompTorquesFineGrain = min(comp_stiffs_ratios):max(comp_stiffs_ratios)/1000:max(comp_stiffs_ratios);

for subs = 1:size(fieldnames(sub_JND_proportion_data),1)
    fields = fieldnames(sub_JND_proportion_data);
    
    for cond = 1:2
        
        NumPos = sub_JND_proportion_data.( fields{subs,1} ).NumPos(cond,:);
        OutofNum = sub_JND_proportion_data.( fields{subs,1} ).OutofNum(cond,:); 
        ProportionForcefulSub = NumPos./OutofNum;
        
        paramsValues = sub_JND_proportion_data.( fields{subs,1} ).paramsValues(cond,:);
        ProportionForcefulModel = PF(paramsValues,CompTorquesFineGrain);
        
        % plot per subject (with incline & decline curve in same figure)
        subplot(1,6,subs);
        if cond == 1
            color = [54 2 89]/255;
        else
            color = [187 166 198]/255;
        end
        plot(CompTorquesFineGrain,ProportionForcefulModel,'-','color',color,'linewidth',4);
        hold on
        plot(comp_stiffs_ratios,ProportionForcefulSub,'.','markersize',40,'Color',color);
        set(gca, 'fontsize',16);
        set(gca, 'Xtick',comp_stiffs_ratios);
        axis([min(comp_stiffs_ratios) max(comp_stiffs_ratios) 0 1]);
        hold on
    end

    xlabel('Fraction of Preferred Stiffness');
    ylabel('Proportion Judged more Forceful');
    legend('Ankle','Ankle Data','Knee','Knee Data','Location','northwest');
    title( sprintf('Subject %d', subj_num(subs)), 'Interpreter','none' );
    box off
    legend boxoff
end

%% Plot Compiled JND Curves across All Subjects for ankle/knee in 2 Separate Figures
close; clc;

figure('name','Plot Per Activity');
CompTorquesFineGrain = 0.3:max(comp_stiffs_ratios)/1000:2;
% color = {'#B589D6', '#9969C7', '#804FAA', '#6A359C', '#552586', '#440150'};

for cond = 1:2
    subplot(1,2,cond);

    % initialize matrices to compute avg psychometric trajectory
    multisubJND = zeros(1,size(fieldnames(sub_JND_proportion_data),1));
    multisubOutofNum = zeros(size(fieldnames(sub_JND_proportion_data),1),length(comp_stiffs_ratios));
    multisubNumPos = zeros(size(fieldnames(sub_JND_proportion_data),1),length(comp_stiffs_ratios));

    for subs = 1:size(fieldnames(sub_JND_proportion_data),1)

        multisubNumPos(subs,:) = sub_JND_proportion_data.( fields{subs,1} ).NumPos(cond,:);
        multisubOutofNum(subs,:) = sub_JND_proportion_data.( fields{subs,1} ).OutofNum(cond,:);

        paramsValues = sub_JND_proportion_data.( fields{subs,1} ).paramsValues(cond,:);
        ProportionForcefulModel = PF(paramsValues,CompTorquesFineGrain);

        multisubJND(1,subs) = sub_JND_proportion_data.( fields{subs,1} ).JND(1,cond);

        % plot per activity
        % plot(CompStiffsFineGrain,ProportionStiffModel,'-','color',color{1,subs},'linewidth',4);
        plot(CompTorquesFineGrain,ProportionForcefulModel,'-','color','#d3d3d3','linewidth',4);

        set(gca, 'fontsize',16);
        hold on
    end

    % Compute averaged JND Trajectory for each activity & overlay on plot
    ProportionStifferAvg = sum(multisubNumPos)./sum(multisubOutofNum);

    slope_est = ( ProportionStifferAvg(6) - ProportionStifferAvg(3) )/( comp_stiffs_ratios(6) - comp_stiffs_ratios(3) );
    searchGrid.beta = logspace(0,10*slope_est,1000);

    disp('Fitting function.....');
    [paramsValues, LL, scenario, exitflag] = PAL_PFML_Fit(comp_stiffs_ratios, sum(multisubNumPos), ...
        sum(multisubOutofNum), searchGrid, paramsFree, PF,'gammaEQlambda',1,'SearchOptions',options);
    
    disp('done:');
    message = sprintf('Slope estimate: %6.4f\r',paramsValues(2));
    disp(message);

    avgdActivityTraj = PF(paramsValues,CompTorquesFineGrain);

    x25 = interp1(avgdActivityTraj, CompTorquesFineGrain, 0.25);
    x75 = interp1(avgdActivityTraj, CompTorquesFineGrain, 0.75);
    avgdJND = (x75-x25)/2;

    % Compute averaged JND trajectory for each activity & overlay on plot
    plot(CompTorquesFineGrain,avgdActivityTraj,'-','color','#804FAA','linewidth',4);

    set(gca, 'Xtick',comp_stiffs_ratios);
    axis([min(comp_stiffs_ratios) max(comp_stiffs_ratios) 0 1]);
    xlabel('Fraction of Preferred Stiffness');
    ylabel('Proportion Judged Stiffer');
    % legend('Subject 101','Subject 102','Subject 105','Subject 106','Subject 107','Subject 108','Average','Location','northwest');
    
    % add dashed lines
    hold on
    plot([x75 x75], [0 0.75], '--','linewidth',3,'color','#808080');
    hold on
    plot([0.8 x75], [0.75 0.75], '--','linewidth',3,'color','#808080');
    txt = ['JND = ' num2str(avgdJND*100,'%.2f') '%'];
    text(1.1,0.15,txt,'FontSize',12,'FontAngle', 'italic')


    if cond == 1
        title('Incline Activity');
        fprintf("Avg JND is: %f for Incline \n", mean(multisubJND));     % Compute average JND for each activity
        fprintf("SEM for JND is: %f for Incline \n", std(multisubJND)/sqrt(subs));
        fprintf("JND from Averaged Trajectory is: %f for Incline \n", avgdJND);    
    elseif cond == 2
        title('Decline Activity');
        fprintf("Avg JND is: %f for Decline \n", mean(multisubJND));
        fprintf("SEM for JND is: %f for Decline \n", std(multisubJND)/sqrt(subs));
        fprintf("JND from Averaged Trajectory is: %f for Incline \n", avgdJND);     
    end
    box off
    % legend boxoff

end

%% Check if JND's are normally distributed - if not, perform bootstrapping?
clc; close all;

for cond = 1:2
    figure()

    multisubJND = zeros(1,size(fieldnames(sub_JND_proportion_data),1));
    for subs = 1:size(fieldnames(sub_JND_proportion_data),1)
        multisubJND(1,subs) = sub_JND_proportion_data.( fields{subs,1} ).JND(1,cond);
    end 
    % histogram of JNDs for each activity
    histogram(multisubJND*100,'BinWidth',2)
    
    if cond == 1
        xlabel('JND (%) for Incline Activity');
    else
        xlabel('JND (%) for Decline Activity');
    end

    ylabel('Number of Subjects');
end

%% Compute Error Estimates for Generated Parameter Values using Bootstrapping

% Number of simulations to determine standard error (Max used 10,000)
B = 10000;
pDevlist = zeros(2,size(fieldnames(sub_JND_proportion_data),1));
Devlist = zeros(2,size(fieldnames(sub_JND_proportion_data),1));
sem_alpha = zeros(2,size(fieldnames(sub_JND_proportion_data),1));
sem_beta = zeros(2,size(fieldnames(sub_JND_proportion_data),1));
all_paramsSims = zeros(2*B,4*size(fieldnames(sub_JND_proportion_data),1));

for subs = 1:size(fieldnames(sub_JND_proportion_data),1)
    fields = fieldnames(sub_JND_proportion_data);
    
    for cond = 1:2
        % Determine standard error
        disp('Determining standard errors.....');
        
        NumPos = sub_JND_proportion_data.( fields{subs,1} ).NumPos(cond,:);
        OutofNum = sub_JND_proportion_data.( fields{subs,1} ).OutofNum(cond,:); 
        paramsValues = sub_JND_proportion_data.( fields{subs,1} ).paramsValues(cond,:);

        searchGrid.alpha = paramsValues(1);
        searchGrid.beta = logspace(0,20*paramsValues(2),10000);
        searchGrid.lambda = 0.02;                % fixed at 0.02 as in ps paper
        searchGrid.gamma = searchGrid.lambda;    % fixed at lapse rate as in methods paper

        options = PAL_minimize('options');
        options.TolFun = 1e-05;
        % maxtries =  10; % max # of tries to retry unconverged resamples (choses new random starting value for the search)
        % rangetries = [0.5 15 0 0]; % range of values centered at paramValues

        [SD, paramsSim, LLSim, converged] = PAL_PFML_BootstrapNonParametric(comp_stiffs_ratios,...
                                            NumPos,OutofNum,paramsValues,paramsFree,B,PF,...
                                            'searchGrid', searchGrid, 'gammaEQlambda', 1, 'SearchOptions', options);
        % [SD, paramsSim, LLSim, converged] = PAL_PFML_BootstrapParametric(...
        %         comp_stiffs_ratios, OutofNum, paramsValues, paramsFree, B, PF, ...
        %         'searchGrid', searchGrid, 'gammaEQlambda', 1, 'SearchOptions', ...
        %         options);

        disp('done:');
        message = sprintf('Standard error of Threshold: %6.4f\r',SD(1));
        message = sprintf('Standard error of Slope: %6.4f\r',SD(2));
        disp(message);
        
        % Number of simulations to perform to determine Goodness-of-Fit
        B_gof = 10000;
        
        disp('Determining Goodness-of-fit.....');
        
        [Dev, pDev] = PAL_PFML_GoodnessOfFit(comp_stiffs_ratios, NumPos, OutofNum, ...
            paramsValues, paramsFree, B_gof, PF, 'searchGrid', searchGrid,'gammaEQlambda', 1);
        
        disp('done:');
        
        % Put summary of results on screen
        message = sprintf('Deviance: %6.4f',Dev);
        disp(message);
        message = sprintf('p-value: %6.4f',pDev);
        disp(message);

        % store the sems, pDevs and Devs for each subject
        pDevlist(cond,subs) = pDev;
        Devlist(cond,subs) = Dev;
        sem_alpha(cond,subs) = SD(1);
        sem_beta(cond,subs) = SD(2);
        if cond == 1
            all_paramsSims(1:B,4*subs-3:4*subs) = paramsSim;
        else
            all_paramsSims(B+1:2*B,4*subs-3:4*subs) = paramsSim;
        end
    end
end