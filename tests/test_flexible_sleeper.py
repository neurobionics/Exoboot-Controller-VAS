import pytest
import time
from src.utils.flexible_sleeper import FlexibleSleeper

def test_flexible_sleeper_pause():
    """
    Test that FlexibleSleeper.pause sleeps for at least the specified period.
    """
    fs = FlexibleSleeper(dt=0.01)
    start = time.perf_counter()
    fs.pause()
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.009

def test_flexible_sleeper_pause_return():
    """
    Test that FlexibleSleeper.pause_return returns a period at least as long as the specified dt.
    """
    fs = FlexibleSleeper(dt=0.01)
    period = fs.pause_return()
    assert period >= 0.009
