import pytest
import numpy as np
import time
from src.utils.walking_simulator import WalkingSimulator

def test_walking_simulator_update_time_in_stride():
    """
    Test WalkingSimulator.update_time_in_stride for incrementing and resetting stride time.
    """
    sim = WalkingSimulator(stride_period=0.1)
    t1 = sim.update_time_in_stride()
    time.sleep(0.05)
    t2 = sim.update_time_in_stride()
    assert t2 >= t1
    # Simulate end of stride
    sim.current_time_in_stride = 0.11
    t3 = sim.update_time_in_stride()
    assert t3 == 0

def test_walking_simulator_update_ank_angle():
    """
    Test WalkingSimulator.update_ank_angle returns a float ankle angle for a given time in stride.
    """
    sim = WalkingSimulator(stride_period=1.2)
    sim.current_time_in_stride = 0.5
    angle = sim.update_ank_angle()
    assert isinstance(angle, float)

def test_time_in_stride_to_percent_GC():
    """
    Test WalkingSimulator.time_in_stride_to_percent_GC for correct percent gait cycle calculation and error on negative input.
    """
    sim = WalkingSimulator(stride_period=1.2)
    assert sim.time_in_stride_to_percent_GC(0.6) == 50
    assert sim.time_in_stride_to_percent_GC(1.2) == 100
    with pytest.raises(ValueError):
        sim.time_in_stride_to_percent_GC(-1)
