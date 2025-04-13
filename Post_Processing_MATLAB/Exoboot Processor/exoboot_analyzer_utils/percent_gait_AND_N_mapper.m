function [N_rep_curve, percent_gc] = percent_gait_AND_N_mapper(HS_idx, N, exo_time)
    % percent_gait_AND_N_mapper -- 
    %   segments heel strike and toe-off event idxs into gait cycles
    %   AND selects a representative transmission ratio curve that maps to
    %   percent gait cycle
    %
    %   percent_gc is a array, as is N_rep_curve that corresponds to the
    %   full exo data stream
    %
    % Author: Nundini Rawal
    % date: 03-27-2025


    percent_gc = nan(size(exo_time));
    N_rep_curve = nan(size(exo_time));
    for gc_i = 1:(length(HS_idx) - 1)
        gc_start = HS_idx(gc_i);
        gc_end = HS_idx(gc_i + 1);
    
        cycle_time = exo_time(gc_start:gc_end);
        cycle_duration = exo_time(gc_end) - exo_time(gc_start);
    
        % Normalize time to 0-1 within this gait cycle
        normd_gc = (cycle_time - cycle_time(1)) / cycle_duration;

        % find the representative TR curve over % GC (idx 3736-4035)
        N_rep_selection = N(3736:4035);

        % interpolate N_rep_selection to be the same size as percent_gc
        x_original = linspace(0, 1, length(N_rep_selection));
        N_interp = interp1(x_original, N_rep_selection, normd_gc);

        % store it
        if gc_i == 1
            percent_gc(gc_start:gc_end) = normd_gc;
            N_rep_curve(gc_start:gc_end) = N_interp;
        else
            percent_gc(gc_start+1:gc_end+1) = normd_gc;
            N_rep_curve(gc_start+1:gc_end+1) = N_interp;
        end
    end
end