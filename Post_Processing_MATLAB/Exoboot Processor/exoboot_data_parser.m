%% 2024-25 Vickrey VAS Study - Determining $-Value over Time
% 
% This code unzips exo-sensor files, stores data in struct, and saves to 
% .mat files for easy processing by exoboot_processor.m script.
% Separate .mat files are generated for each session type: Vickrey EPO,
% Preference, VAS I/II/III. Struct fieldnames include: left_exo, right_exo,
% GSE.
% 
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/Exoboot Processor directory
% Author: Nundini Rawal
% Date: 2/10/2025

clc; close; clearvars -except subject subject_list exoboot_compiled_data

%% Ask for path to VAS subject file tree

prompt = "Which Data to Parse: (VAS/Pref/Vickrey)\n";
sesh_2_parse = input(prompt,"s");

base_path = '/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/';

fprintf("Select Location of the %s File Tree\n", sesh_2_parse);
path = append(base_path,'VAS_Protocol_Data/');
directory_path = uigetdir(path);

% ask for path to subject dictionary file tree
fprintf("Select Location of the subject dictionary file\n");
sub_dict_path = base_path;
[~,sub_dictionary_file_location] = uigetfile(sub_dict_path);

% add data file directory & subject dictionary to path
addpath(genpath(directory_path))
addpath(genpath(sub_dictionary_file_location))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

%% specify subj numbers (remove subjects due to any criteria) & parser util
subj_num = [5];
parser_util = exoboot_parser_utils();

%% Parse selected session type

if sesh_2_parse == "VAS"
    exoboot_compiled_data = parser_util.VAS_exoboot_data_packager(subj_num, subject);
elseif sesh_2_parse == "Vickrey"
    exoboot_compiled_data = parser_util.Vickrey_exoboot_data_packager(subj_num, subject);
elseif sesh_2_parse == "Pref"
    exoboot_compiled_data = parser_util.Pref_exoboot_data_packager(subj_num, subject);
else
    fprintf("Session type DNE")
end

fprintf(" ~~ Exoboot data parsing and .mat packaging complete! ~~\n");
