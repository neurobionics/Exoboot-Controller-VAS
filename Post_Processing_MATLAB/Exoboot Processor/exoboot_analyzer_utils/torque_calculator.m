function calculated_torque = torque_calculator(I, N, kt)
    % torque_calculator
    %   Applies the motor model to calculate the output torque using the current. 
    %
    %   Author: Nundini Rawal
    %   date: 3/25/2025
    
    calculated_torque = kt*I.*N;
end