import pytest
from src.utils.filing_utils import get_user_inputs, get_logging_info
from unittest import mock
import sys

# Test get_user_inputs (simulate argparse)
def test_get_user_inputs(monkeypatch):
    """
    Test get_user_inputs by simulating command-line arguments and checking
    that the returned values match the expected file name and parameters.
    """
    test_args = ["prog", "--sub", "123", "--trial-type", "testtype", "--trial-cond", "cond", "--desc", "20250101", "--backup", "True"]
    monkeypatch.setattr(sys, 'argv', test_args)
    result = get_user_inputs()
    assert result[0].startswith("S123_testtype_cond_20250101_exothread")
    assert result[1] == "S123"
    assert result[2] == "testtype"
    assert result[3] == "cond"
    assert result[4] == 20250101 or str(result[4]) == "20250101"
    assert result[5] is True or result[5] == "True"

# Test get_logging_info (no input)
def test_get_logging_info_no_input():
    """
    Test get_logging_info with use_input_flag set to False, expecting default log path and file name.
    """
    log_path, file_name = get_logging_info(False)
    assert log_path == "./src/logs/"
    assert file_name == "tracking_test"
