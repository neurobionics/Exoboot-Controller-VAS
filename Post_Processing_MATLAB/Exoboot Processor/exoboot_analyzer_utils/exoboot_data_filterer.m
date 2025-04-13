function [filtered_output] = exoboot_data_filterer(data,freq, cutoff_freq, cutoff_power)
    % exoboot_data_filterer
    %   Identifies the dominant frequencies in provided signal using
    %   power spectral density plot. Then removes unwanted parts of the
    %   signal. Outputs the cleaned signal in the time domain.
    %
    %   Author: Nundini Rawal
    %   date: 3/25/2025
    
    fft_ddx_accel_y = fft(data);
    n = length(data);                   % number of samples
    max_fs = max(freq);                 % max freq
    freq_vec = (0:n-1)*(max_fs/n);      % frequency range
    power = abs(fft_ddx_accel_y).^2/n;  % 1-sided power of the DFT

    % filter out the data signal
    cutoff_fs = cutoff_freq;                  % Hz
    cutoff_pwr = cutoff_power;                % power
    freq_idxs = find( ( (freq_vec >= 25) & (freq_vec <= 75) ) );
    PSD_idxs = find(power >= cutoff_pwr);
    clean_idxs = intersect(PSD_idxs, freq_idxs);

    % zero out the unwanted noisy components
    filtd_fft = fft_ddx_accel_y(clean_idxs);
    num_freq_removed = n-length(filtd_fft);
    filtd_fft = [filtd_fft; zeros(num_freq_removed,1)];
    filtd_power = abs(filtd_fft).^2/n;  % 1-sided power of the DFT

    % plot original and denoised power spectrum
    figure;
    plot(freq_vec,power); hold on;
    plot(freq_vec,filtd_power);
    xlabel('Frequency')
    ylabel('Power')
    legend('original','clean signal')

    % obtain the filtered signal back in time domain
    filtered_output = real(ifft(filtd_fft));
end