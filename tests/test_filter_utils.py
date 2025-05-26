import pytest
from src.utils.filter_utils import MovingAverageFilter, TrueAfter, MovingAverageFilterPlus, PID

def test_moving_average_filter():
    """
    Test MovingAverageFilter for correct average calculation after updates.
    """
    f = MovingAverageFilter(initial_value=1, size=3)
    assert f.average() == 1
    f.update(2)
    f.update(3)
    assert abs(f.average() - 2) < 1e-6
    f.update(4)
    assert abs(f.average() - (2+3+4)/3) < 1e-6

def test_true_after():
    """
    Test TrueAfter to ensure it returns True only after the specified number of steps.
    """
    t = TrueAfter(after=2)
    assert not t.isafter()
    t.step()
    assert not t.isafter()
    t.step()
    assert not t.isafter()
    t.step()
    assert t.isafter()

def test_moving_average_filter_plus():
    """
    Test MovingAverageFilterPlus for average and trimmed average calculations.
    """
    f = MovingAverageFilterPlus(cold_start=False, initial_value=2, size=3)
    assert abs(f.average() - 2) < 1e-6
    f.update(4)
    f.update(6)
    assert abs(f.average() - (2+4+6)/3) < 1e-6
    # Test trimmed_average
    assert abs(f.trimmed_average() - (2+4)/2) < 1e-6

def test_pid():
    """
    Test PID controller output for different setpoints and measured values.
    """
    pid = PID(Kp=1, Kd=0.1, Ki=0.01)
    out1 = pid.update(10, 8, 1)
    out2 = pid.update(10, 9, 1)
    assert isinstance(out1, float)
    assert isinstance(out2, float)
    assert out1 != out2
