import pytest, datetime

from src.settings.constants import DETROIT_TIMEZONE, DATETIME_FORMAT_LESS_SEC, PREFIX_FORMAT_GENERIC, FILENAME_FORMAT

from src.logger.filing_cabinet_regex import build_prefix, build_filename

current_date = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMAT_LESS_SEC)
subject = "TESTER"
trialtype = "VICKREY"
condition1 = "EPO"
condition2 = "BOO"

def test_build_prefix_not_enough_args():
    with pytest.raises(KeyError):
        build_prefix()

def test_build_prefix_basic():
    prefix_2arg = build_prefix(prefix_format=PREFIX_FORMAT_GENERIC, SUBJECT=subject, TRIALTYPE=trialtype)
    prefix_3arg_c1 = build_prefix(prefix_format=PREFIX_FORMAT_GENERIC, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1)
    prefix_3arg_c2 = build_prefix(prefix_format=PREFIX_FORMAT_GENERIC, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION2=condition2)
    prefix_4arg = build_prefix(prefix_format=PREFIX_FORMAT_GENERIC, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)

    assert prefix_2arg == "TESTER_VICKREY"
    assert prefix_3arg_c1 == "TESTER_VICKREY_EPO"
    assert prefix_3arg_c2 == "TESTER_VICKREY_BOO"
    assert prefix_4arg == "TESTER_VICKREY_EPO_BOO"

def test_build_prefix_different_PREFIX_FORMAT_GENERIC():
    # Prefix format with swapped SUBJECT, TRIALTYPE order
    # and extraneous CONDITION3
    new_prefix_format = r'%TRIALTYPE_%SUBJECT_%CONDITION1_%CONDITION2_%CONDITION3'

    prefix_2arg = build_prefix(prefix_format=new_prefix_format, SUBJECT=subject, TRIALTYPE=trialtype)
    prefix_3arg_c1 = build_prefix(prefix_format=new_prefix_format, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1)
    prefix_3arg_c2 = build_prefix(prefix_format=new_prefix_format, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION2=condition2)
    prefix_4arg = build_prefix(prefix_format=new_prefix_format, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)

    assert prefix_2arg == "VICKREY_TESTER"
    assert prefix_3arg_c1 == "VICKREY_TESTER_EPO"
    assert prefix_3arg_c2 == "VICKREY_TESTER_BOO"
    assert prefix_4arg == "VICKREY_TESTER_EPO_BOO"

def test_build_prefix_different_and_long_separators():
    new_prefix_format = r'%TRIALTYPE__%SUBJECT?_%CONDITION1^^^^^%CONDITION2+++%CONDITION3'
    prefix = build_prefix(prefix_format=new_prefix_format, SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)
    assert prefix == "VICKREY__TESTER?_EPO^^^^^BOO"


def test_build_filename_basic():
    prefix = build_prefix(SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1)
    filename = build_filename(FORMAT=FILENAME_FORMAT, PREFIX=prefix, DATE=current_date, SUFFIX="exothread_left", EXT="csv")
    assert filename == f"TESTER_VICKREY_EPO_{current_date}_exothread_left.csv"

def test_build_filename_missing_argument():
    with pytest.raises(KeyError):
        build_filename(FORMAT=FILENAME_FORMAT, DATE=current_date, SUFFIX="exothread_left", EXT="csv")