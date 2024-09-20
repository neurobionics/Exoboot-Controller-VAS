function csv_combiner(input_path, output_file)
% CSV_COMBINER: Joins multiple csvs together 
%   Only combines csv files within the same navigated directory and assumes
%   column-oriented data. Reads each .csv file in the input_path location
%   into a table which is then storedin a cell array of tables called by
%   the output_file name.
%
%   Inputs: 
%       input_path - location of the .csv files
%       output_file - name of file containing combined data
%
%   Author: Nundini Rawal
%   date: 9/19/24


% specify lab drive location:
lab_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';
full_path = lab_path + input_path;

% 
file_info = dir(fullfile(full_path,'*.csv'));
full_file_names = fullfile(full_path,{file_info.name});
n_files = numel(file_info);
all_data = cell(1,n_files);
for ii = 1:n_files
    all_data{ii} = readtable(full_file_names{ii});
end

% concatenate all the tables into one big table, and write it to
% output_file:
writetable(cat(1,all_data{:}),output_file);

% check that the resulting output file exists:
dir('*.csv')
end