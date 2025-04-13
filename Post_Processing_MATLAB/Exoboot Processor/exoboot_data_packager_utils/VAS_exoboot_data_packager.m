function exoboot_compiled_data = VAS_exoboot_data_packager(subj_num, subject)
    % VAS_exoboot_data_packager -- 
    %   Extract files from zip-archive for VAS I, II,III
    %
    % Author: Nundini Rawal
    % Date: 02-25-2025
    
    exoboot_compiled_data = struct();
    
    for sub_num = subj_num
    
        per_sub_data_zip_name = subject(sub_num).VAS_exo_sensor_filenames;
    
        for zip_idx = 1:length(per_sub_data_zip_name)
    
            % if folder DNE
            if exist("local_temp_processing_folder/") == 0
                % unzip the folder
                per_sub_data_fnames = unzip(per_sub_data_zip_name{zip_idx}, 'local_temp_processing_folder');
                addpath(genpath('local_temp_processing_folder/'));

                % remove .DS_Store
                index = find(contains(per_sub_data_fnames,'.DS_Store'));

                if isempty(index)
                    per_sub_data_fnames = per_sub_data_fnames(1,2:end);
                else
                    per_sub_data_fnames = per_sub_data_fnames(1,index+1:end);
                end
                
            else
                addpath(genpath('local_temp_processing_folder/'));
    
                % determine which session number
                dir_session_num = struct2table(dir('local_temp_processing_folder/'));
                dir_session_num = char(dir_session_num{3,1});
                
                % determine filenames in existing temp folder
                dir_desc = dir(append('local_temp_processing_folder/', dir_session_num));
                temp_dir_desc_tbl = struct2table(dir_desc);
    
                folders = temp_dir_desc_tbl(~temp_dir_desc_tbl.isdir,:);
                per_sub_data_fnames = folders.name;
            end
    
            % loop through files, and fill struct with data per group
            for file_idx = 1:length(per_sub_data_fnames)
                xls_sheet = per_sub_data_fnames{file_idx};
                exo_data_sheet = readtable(xls_sheet);
    
                % based on fname, determine group # & whether file is left/right/GSE
                group_number = string(extract(extract(xls_sheet, regexpPattern("(?i)group\d+")), digitsPattern));
                cond = extract(xls_sheet, "left"|"right"|"GSE");
    
                % if contains '_new' suffix, append to cond
                pat = "_new";
                new_suffix = string(extract(xls_sheet,pat));

                num_of_suffixes = size(new_suffix,1);
                if num_of_suffixes > 1
                    alt_suffix = "";
                    for i = 1:num_of_suffixes
                        alt_suffix = alt_suffix + new_suffix{i};
                    end
                    new_suffix = alt_suffix;
                end

                % create fieldnames dynamically for struct
                if isempty(new_suffix)
                    cond_type_field = string(cond{1,1});
                else
                    cond_type_field = string(cond{1,1}) + string(new_suffix);
                end
                
                subject_field = "S10" + sub_num;
                group_field = "group" + group_number;
                
                % if subject field doesn't exist, initialize empty struct
                if ~isfield(exoboot_compiled_data, subject_field)
                    exoboot_compiled_data.(subject_field) = struct();
                end
    
                % store the data in struct
                exoboot_compiled_data.(subject_field).(group_field).(cond_type_field) = exo_data_sheet;
            end
    
            % delete the temporary storage folder
            rmdir('local_temp_processing_folder/','s')
            
        end
    end
    
    mat_fname = "S10" + subj_num + "_VAS_exoboot_data.mat";
    zip_fname = "S10" + subj_num + "_zipped_VAS_exoboot_data";

    % save the struct in a .mat file for easy loading in the future
    save(mat_fname, '-struct', 'exoboot_compiled_data');

    % compress the file
    zip(zip_fname, mat_fname);

    % remove the unzipped struct
    delete (mat_fname)
end
