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
    assert abs(f.average() - (1+2+3)/3) < 1e-6
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
    assert abs(f.average() - (2+2+2)/3) < 1e-6
    f.update(4)
    f.update(6)
    assert abs(f.average() - (2+4+6)/3) < 1e-6
    
    # Test trimmed_average (removing 6)
    assert abs(f.trimmed_average() - (2+4)/2) < 1e-6
