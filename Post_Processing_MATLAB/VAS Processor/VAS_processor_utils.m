classdef VAS_processor_utils
    % Utils Summary
    %   Contains Functions to help parse the Value Landscape data
    %   Pairs with VAS_analyzer.m
    %   Written by: Nundini Rawal (1/15/2025)

    properties
        Property1
    end

    methods
        function obj = VAS_processor_utils()
            % VAS_PROCESSOR_UTILS
            %   __init__ method to set-up instance
        end

        function modified_datasheet = set_Header_101_to_103_ONLY(obj,data_sheet)
            % SET_HEADER -- Renames the Header of the raw VAS data file 
            %   Renames in case they are misnamed or not detected.
            %   Sheet naming is 'btn', 'trial', 'pres', 'torque1', 'mv1'...
            
            torque_numbering = 4:2:width(data_sheet);
            value_numbering = 5:2:width(data_sheet);
            torque_headers = append("torque",string(1:length(torque_numbering)));
            value_headers = append("mv",string(1:length(torque_numbering)));
            
            data_sheet = renamevars(data_sheet,torque_numbering,torque_headers);
            data_sheet = renamevars(data_sheet,value_numbering,value_headers);
            data_sheet = renamevars(data_sheet,1:3, ["btn_option","trial","pres"]);

            modified_datasheet = data_sheet;
        end

            function modified_datasheet = set_Header(obj,data_sheet)
            % SET_HEADER -- Renames the Header of the raw VAS data file 
            %   Renames in case they are misnamed or not detected.
            %   Sheet naming is 'session', 'group', 'btn', 'pres', 'torque1', 'mv1'...
            
            torque_numbering = 5:2:width(data_sheet);
            value_numbering = 6:2:width(data_sheet);
            torque_headers = append("torque",string(1:length(torque_numbering)));
            value_headers = append("mv",string(1:length(torque_numbering)));
            
            data_sheet = renamevars(data_sheet,torque_numbering,torque_headers);
            data_sheet = renamevars(data_sheet,value_numbering,value_headers);
            data_sheet = renamevars(data_sheet,1:4, ["session","group","btn_option","pres"]);

            modified_datasheet = data_sheet;
        end


        function [btn_select_indxs, answer_norm, btn_field_func_map] = get_user_input(obj,list)
            % GET_USER_INPUT -- Allows for users to select btns to plot,
            %   whether to normalize data, and whether to plot data in a
            %   single figure. 
            
            btn_select_indxs = listdlg('PromptString',{'Select a btn type to plot.',...
                                    'Multiselect is possible.',''},...
                                    'SelectionMode','multiple', ...
                                    'ListString',list, ...
                                    'ListSize', [150 50]);

            prompt = {'Operate with Normalized Data? (y/n):'};

            dlgtitle = 'VAS Protocol Plotting Inputs';
            fieldsize = [1 45];
            default_input = {'y'};
            answer = inputdlg(prompt,dlgtitle,fieldsize,default_input);
            
            % use inputs to set vars:
            answer_norm = answer{1};

            % obtain button field mapping
            btn_field_func_map = obj.create_btn_field_func_map();

        end

        function btn_field_func_map = create_btn_field_func_map(obj)
            % CREATE_BTN_FIELD_FUNC_MAP -- Links user plotting selection
            %   with button type and corresponding struct un-wrapper
            
            btn_field_func_map = containers.Map({1, 2, 3},{...
                                        {'VAS_filename_1BTN', @obj.unpack_1BTN}, ...
                                        {'VAS_filename_4BTN', @obj.unpack_4BTN}, ...
                                        {'VAS_filename_10BTN', @obj.unpack_10BTN} ...
                                        });
        end


        function [reshaped_torques, reshaped_values, total_options, ...
                    max_group_num] = unpack_field_func_pair(obj,compiled_data,...
                        sub_num,btn_field_func_map,curr_btn_opt_idx)
            % UNPACK_FIELD_FUNC_PAIR -- Unpacks proper btn data & fcn
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num
            
            if isKey(btn_field_func_map, curr_btn_opt_idx)
                mapping = btn_field_func_map(curr_btn_opt_idx);
                btn_field_name = mapping{1}; 
                unpack_func = mapping{2};
         
                if isfield(compiled_data.("S10" + sub_num), btn_field_name)
                    [reshaped_torques, reshaped_values, total_options, ...
                            max_group_num] = unpack_func(compiled_data, sub_num);
                end
            end
        end


        function [reshaped_torques, reshaped_values, total_options, ...
                max_group_num] = unpack_1BTN(obj,compiled_data,sub_num)
            % UNPACK_4BTN -- Unpacks 1btn subject data 
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num

            reshaped_torques = compiled_data.("S10" + sub_num).VAS_filename_1BTN.reshaped_torques;
            reshaped_values = compiled_data.("S10" + sub_num).VAS_filename_1BTN.reshaped_values;
            total_options = compiled_data.("S10" + sub_num).VAS_filename_1BTN.total_options;
            max_group_num = compiled_data.("S10" + sub_num).VAS_filename_1BTN.max_group_num;
        end

        function [reshaped_torques, reshaped_values, total_options, ...
                max_group_num] = unpack_4BTN(obj,compiled_data,sub_num)
            % UNPACK_4BTN -- Unpacks 4btn subject data 
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num

            reshaped_torques = compiled_data.("S10" + sub_num).VAS_filename_4BTN.reshaped_torques;
            reshaped_values = compiled_data.("S10" + sub_num).VAS_filename_4BTN.reshaped_values;
            total_options = compiled_data.("S10" + sub_num).VAS_filename_4BTN.total_options;
            max_group_num = compiled_data.("S10" + sub_num).VAS_filename_4BTN.max_group_num;
        end

        function [reshaped_torques, reshaped_values, total_options,...
                max_group_num] = unpack_10BTN(obj,compiled_data,sub_num)
            % UNPACK_10BTN -- Unpacks 10btn subject data from compiled_data struct 
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num

            reshaped_torques = compiled_data.("S10" + sub_num).VAS_filename_10BTN.reshaped_torques;
            reshaped_values = compiled_data.("S10" + sub_num).VAS_filename_10BTN.reshaped_values;
            total_options = compiled_data.("S10" + sub_num).VAS_filename_10BTN.total_options;
            max_group_num = compiled_data.("S10" + sub_num).VAS_filename_10BTN.max_group_num;
        end

        function [reshaped_torques, reshaped_values, total_options, ...
                max_group_num] = unpack_4BTN_S101_to_S103_ONLY(obj,compiled_data,sub_num)
            % UNPACK_4BTN -- Unpacks 4btn subject data 
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num

            reshaped_torques = compiled_data.("S10" + sub_num).VAS_filename_4BTN.reshaped_torques;
            reshaped_values = compiled_data.("S10" + sub_num).VAS_filename_4BTN.reshaped_values;
            total_options = compiled_data.("S10" + sub_num).VAS_filename_4BTN.total_options;
            max_group_num = compiled_data.("S10" + sub_num).VAS_filename_4BTN.max_trial_num;
        end

        function [reshaped_torques, reshaped_values, total_options,...
                max_group_num] = unpack_10BTN_S101_to_S103_ONLY(obj,compiled_data,sub_num)
            % UNPACK_10BTN -- Unpacks 10btn subject data from compiled_data struct 
            %   Outputs: reshaped_torques, reshaped_values,...
            %       reshaped_values, max_group_num

            reshaped_torques = compiled_data.("S10" + sub_num).VAS_filename_10BTN.reshaped_torques;
            reshaped_values = compiled_data.("S10" + sub_num).VAS_filename_10BTN.reshaped_values;
            total_options = compiled_data.("S10" + sub_num).VAS_filename_10BTN.total_options;
            max_group_num = compiled_data.("S10" + sub_num).VAS_filename_10BTN.max_trial_num;
        end

        function [normd_data] = normalize_data(obj, data)
            % NORMALIZE_DATA -- Performs min-max normalization 
            %   Outputs: Takes matrix data & finds global max & min with
            %       which to normalize with
            
            global_min = min(data,[],'all');
            global_max = max(data,[],'all');

            normd_data = (data - global_min)/(global_max - global_min);
        end

        function [LMEM_full_table] = LMEM_VAS_constructor(obj,subj_num,compiled_data, answer)
            % LMEM_VAS_CONSTRUCTOR -- Creates Tables for Linear Mixed Effects Modeling 
            %   Outputs 1 compiled 4BTN table with the following headings:
            %       participants, trial, pres, torques, values

            participants = [];
            trials = [];
            presentations = [];
            torques = [];
            values = [];
            LMEM_full_table = table;

            for sub_num = subj_num
                % open each subject's struct
                sub_specific_data = compiled_data.("S10" + sub_num).VAS_filename_4BTN;

                torques_per_trial = sub_specific_data.total_options;
                num_trials = sub_specific_data.max_trial_num;
                torques_per_pres = 4;
                pres_per_trial = torques_per_trial/torques_per_pres;

                % determine participant repetition
                total_entries = torques_per_trial*num_trials;
                participant = repelem(sub_num, total_entries)';
                
                % determine pres repetition
                base_pres_namimg = append( string(1:pres_per_trial), 'p' );
                base_pres = repelem(base_pres_namimg, torques_per_pres)';
                pres = repmat(base_pres,num_trials,1);
                
                % determine trial repetition
                base_trial_namimg = append( string(1:num_trials), 't' );
                trial = repelem(base_trial_namimg, torques_per_trial)';

                if answer == "y"
                    torque_output = obj.normalize_data(sub_specific_data.reshaped_torques);
                    value_output = obj.normalize_data(sub_specific_data.reshaped_values);
                else
                    torque_output = sub_specific_data.reshaped_torques;
                    value_output = sub_specific_data.reshaped_values;
                end

                % determine torque repetition
                sub_torques = reshape(torque_output,[],1);

                % determine value repetition
                sub_values = reshape(value_output,[],1);

                % append each to their respective vectors
                participants = [participants;participant];
                trials = [trials;trial];
                presentations = [presentations;pres];
                torques = [torques;sub_torques];
                values = [values;sub_values];
            end

            % convert to categorical variables & assign to table 
            LMEM_full_table.participants = string(participants);
            LMEM_full_table.trials = trials;
            LMEM_full_table.presentations = presentations;
            LMEM_full_table.torques = torques;
            LMEM_full_table.values = values;

            % remove entries for trial 5 for S103
            LMEM_full_table = LMEM_full_table(1:240,:);

        end

        function [filtered_table] = LMEM_table_shifter(obj,full_table,options)
            % LMEM_TABLE_FILTERER -- Reorders tables according to selected arguments 
            %    Optional Args:
            %       analysis_type = "intersubject"/"intrasubject"
            %       filt_type = "trial"/"pres"
            %       trial_or_pres = numeric type
            %       sub = numeric type

            arguments       
                obj VAS_processor_utils         
                full_table table
                options.analysis_type string = "intersubject"
                options.filt_type string = "trial"
                options.trial_or_pres {mustBeNumeric}
                options.sub {mustBeNumeric}
            end

            if options.filt_type == "trial"
                shift_const = 20;
            elseif options.filt_type == "pres"
                shift_const = 4;
            end

            if options.analysis_type == "intersubject"

                if options.trial_or_pres ~= 1
                    filtered_table = table;
    
                    % for each subject,
                    for sub = 1:3
                        % extract the subject-specific data into table A and rename it depending on subject number
                        sub_spec_table = obj.LMEM_table_sub_filterer(full_table, sub);
    
                        % circshift the table by trial
                        shift_amnt = -shift_const*(options.trial_or_pres-1);
                        shifted_table = circshift(sub_spec_table,shift_amnt);
    
                        % append to end table
                        filtered_table = [filtered_table; shifted_table];
                    end
    
                    full_table = filtered_table;
                end
    
                filtered_table = full_table;
            
            elseif options.analysis_type == "intrasubject"
    
                % extract the subject-specific data into table A and rename it depending on subject number
                sub_spec_table = obj.LMEM_table_sub_filterer(full_table, options.sub);

                % circshift the table by trial
                shift_amnt = -shift_const*(options.trial_or_pres-1);
                shifted_table = circshift(sub_spec_table,shift_amnt);

                % append to end table
                filtered_table = shifted_table;
            end

        end


        function [output_table] = LMEM_table_sub_filterer(obj,table,sub)
            % LMEM_TABLE_SUB_FILTERER -- Extract table according to provided subject number 
            %    Extract data for a particular subject from the provided table

            num_of_trials = 4;
            total_torques = 20;
            
            per_sub_entries = total_torques*num_of_trials;
            start_cut_idx = per_sub_entries*(sub-1)+1;
            end_cut_idx = start_cut_idx + per_sub_entries - 1;
            output_table = table(start_cut_idx:end_cut_idx, :);
        end

        function [output_table] = LMEM_table_trial_filterer(obj,full_table,trial)
            % LMEM_TABLE_TRIAL_FILTERER -- Extract table according to provided trial number 
            %    Extract data for a particular trial across all subs from the provided table
            
            output_table = table;
            per_trial_entries = 20;
            for sub = 1:3
                % per subject extract selected trial
                sub_filtered_table = obj.LMEM_table_sub_filterer(full_table,sub);

                start_cut_idx = per_trial_entries*(trial-1)+1;
                end_cut_idx = start_cut_idx + per_trial_entries - 1;
                trial_filt_table = sub_filtered_table(start_cut_idx:end_cut_idx, :);

                % append to end table
                output_table = [output_table; trial_filt_table];
            end
        end
    end
end