function valid_gait_cycles = gait_cycle_segmenter(HS_idx, T_stride_min, T_stride_max, ...
    fp_interp, ank_ang, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, ...
    peak_torque, mot_curr, N, exo_time, TO_idx, calculated_torque)

    % gait_cycle_segmenter -- 
    %   segments heel strike and toe-off event idxs into gait cycles
    %   saves data into a struct with cells as separate gait cycles
    %
    % Author: Nundini Rawal
    % date: 03-27-2025

    % Count the number of valid gait cycles first
    valid_count = 0;
    for hs_i = 1:length(HS_idx) - 1
        gc_start = HS_idx(hs_i);
        gc_end = HS_idx(hs_i + 1);
    
        % Compute the stride period
        act_stride_time = exo_time(gc_end) - exo_time(gc_start);
        
        % Check if it is valid
        if (act_stride_time >= T_stride_min) && (act_stride_time <= T_stride_max)
            valid_count = valid_count + 1;
        end
    end
    
    % Initialize a struct with empty cell arrays
    valid_gait_cycles = struct(...
        'time', {{}}, ...
        'fp', {{}}, ...
        'ankle_angle', {{}}, ...
        'TO_idx', {{}}, ...
        'gyro_x', {{}}, ...
        'gyro_y', {{}}, ...
        'gyro_z', {{}}, ...
        'accel_x', {{}}, ...
        'accel_y', {{}}, ...
        'accel_z', {{}}, ...
        'peak_torque', {{}}, ...
        'mot_curr', {{}}, ...
        'N', {{}}, ...
        'calculated_torque', {{}});
    
    figure; hold on
    valid_idx = 0;
    is_valid = 0;
    for hs_i = 1:length(HS_idx) - 1
        gc_start = HS_idx(hs_i);
        gc_end = HS_idx(hs_i + 1);
    
        % Compute the stride period
        act_stride_time = exo_time(gc_end) - exo_time(gc_start);
        
        % Skip invalid strides
        if (act_stride_time < T_stride_min) || (act_stride_time > T_stride_max)
            is_valid = 0;
        else
            is_valid = 1;
        end
    
        if is_valid
            % Increment valid index
            valid_idx = valid_idx + 1;
        
            % Store each gait cycle as a matrix in a cell array
            valid_gait_cycles.time{valid_idx,1} = exo_time(gc_start:gc_end);
            valid_gait_cycles.fp{valid_idx,1} = fp_interp(gc_start:gc_end);
            valid_gait_cycles.ankle_angle{valid_idx,1} = ank_ang(gc_start:gc_end);
            
            valid_gait_cycles.TO_idx{valid_idx,1} = TO_idx;  % Store the toe-off index
        
            % Assign IMU and force data
            valid_gait_cycles.gyro_x{valid_idx,1} = gyro_x(gc_start:gc_end);
            valid_gait_cycles.gyro_y{valid_idx,1} = gyro_y(gc_start:gc_end);
            valid_gait_cycles.gyro_z{valid_idx,1} = gyro_z(gc_start:gc_end);
        
            valid_gait_cycles.accel_x{valid_idx,1} = accel_x(gc_start:gc_end);
            valid_gait_cycles.accel_y{valid_idx,1} = accel_y(gc_start:gc_end);
            valid_gait_cycles.accel_z{valid_idx,1} = accel_z(gc_start:gc_end);
        
            valid_gait_cycles.peak_torque{valid_idx,1} = peak_torque(gc_start:gc_end);
            valid_gait_cycles.mot_curr{valid_idx,1} = mot_curr(gc_start:gc_end);
            valid_gait_cycles.N{valid_idx,1} = N(gc_start:gc_end);
            valid_gait_cycles.calculated_torque{valid_idx,1} = calculated_torque(gc_start:gc_end);
        end

        % Plot gait cycles
        if is_valid
            % Valid gait cycles in green
            plot(exo_time(gc_start:gc_end), fp_interp(gc_start:gc_end), 'g-', 'LineWidth', 1.5, 'DisplayName', 'Valid GC');
            hold on
        else
            % Invalid gait cycles in red
            plot(exo_time(gc_start:gc_end), fp_interp(gc_start:gc_end), 'r-', 'LineWidth', 1.5, 'DisplayName', 'Invalid GC');
            hold on
        end
    end

    xlabel('Time (s)');
    ylabel('Force (N)');
    grid on;
    hold off;
end