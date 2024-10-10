%% 2024-25 Vickrey VAS Study - Post-Processes Exoboot Sensor Streams
% This code plots:
% (1) 
% (2) 
%
% Script should be run from the Exoboot-Controller-VAS/Post_Processing_MATLAB/Exploration Strategy Processor directory
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
[~,sub_dictionary_file_location] = uigetfile;

% add VAS directory & subject dictionary to path
addpath(genpath(VAS_directory_path))
addpath(genpath(sub_dictionary_file_location))

% loading in subject info from dictionary
[subject, subject_list] = subject_dictionary_VAS;

% specify subj numbers (remove subjects due to any criteria)
subj_num = [2 3];