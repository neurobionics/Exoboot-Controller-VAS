import pytest
import time
from src.utils.flexible_sleeper import FlexibleSleeper

def test_flexible_sleeper_pause():
    """
    Test that FlexibleSleeper.pause sleeps for ATLEAST the specified period.
    """
    fs = FlexibleSleeper(dt=0.01)
    start = time.perf_counter()
    fs.pause()
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.009

def test_flexible_sleeper_pause():
    """
    Test that FlexibleSleeper.pause sleeps for NO MORE THAN 10% more than specified period.
    """
    dt = 0.01
    fs = FlexibleSleeper(dt=dt)
    start = time.perf_counter()
    fs.pause()
    elapsed = time.perf_counter() - start
    upper_thresh = 1.10*dt
    
    assert elapsed <= upper_thresh