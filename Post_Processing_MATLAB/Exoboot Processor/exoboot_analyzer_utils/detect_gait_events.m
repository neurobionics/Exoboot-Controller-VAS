function [HS_idx,TO_idx] = detect_gait_events(fp_data, threshold)
    % detect_gait_events --
    %   detect gait events(heel-strike and toe-off) from force plate data
    % 
    % Author: Nundini Rawal
    % date: 03-27-2025

    HS_idx = find(diff(fp_data > threshold) == 1); % Heel strike (GRF rising)
    TO_idx = find(diff(fp_data > threshold) == -1); % Toe off (GRF falling)

end