
addpath(genpath('/Volumes/me-neurobionics/Lab Members/Students/Nundini Rawal/SUBJECT DATA/Vickrey_Data_Analysis/VAS_Protocol_Data/VAS Pilot Data/Pilot/Jace_Pilot/'))

%% display jace


%% riley data

T1_Assistance = [10, 36.67, 16.67, 13.33, 6.67, 23.33, 3.33, 26.67, 40, 33.33, 30, 20];
T1_Value = [-14.43, -0.99, -8.89, -12.18, -15.58, -0.5, -13.13, -1.42, 0.5, -7.82, -1.27, -14.28];

T2_Assistance = [33.3, 20, 16.67, 26.67, 6.67, 36.67, 3.33, 13.33, 10, 23.33, 40, 30];
T2_Value = [-14.29, -10.27, -3.16, -4.79, -17.45, -14.05, -8.01, -9.09, -13.49, -5.26, -1.54, -2.39];

T3_Assistance = [20, 16.67, 6.67, 10, 40, 23.33, 26.67, 3.33, 13.33, 33.33, 30, 36.67];
T3_Value =[-1.42, -4.01, -18.07, -13.74, 0.93, -6.33, -3.34, -17.43, -15.66, -4.39, -2.93, -0.12];

figure()
plot(T1_Assistance, T1_Value, 'ob', T2_Assistance,T2_Value, 'or', T3_Assistance, T3_Value, 'og')
xlabel("Torque (Nm)")
ylabel("$/Hour")
title("Riley Landscape")










