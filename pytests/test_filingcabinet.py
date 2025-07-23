import os
import datetime
import shutil
import pytest
from pathlib import Path
from src.logger.filing_cabinet import FilingCabinet
from src.logger.filing_cabinet_regex import build_prefix, build_filename
from src.settings.constants import DETROIT_TIMEZONE, DATETIME_FORMAT_LESS_SEC, FILENAME_FORMAT, PREFIX_FORMAT_GENERIC

test_dir = "test_subject_data"

def setup_module(module):
    os.makedirs(test_dir, exist_ok=True)


def test_folder_hierarchy_creation():
    """Test if the FilingCabinet creates the folder hierarchy correctly."""
    cabinet = FilingCabinet("root", test_dir, "subj1")
    assert os.path.isdir(cabinet.getparentfolderpath())


def test_newfile_creates_unique_file():
    """Test if a unique file is created when the same name is used to create a file.
    Ensures that the new file has a "-new" suffix at the end to prevent conflicts."""
    cabinet = FilingCabinet("root", test_dir, "subj2")
    filename = "data.txt"
    uid = "data"
    file1 = cabinet.newfile(filename, uid)
    Path(file1).touch()
    file2 = cabinet.newfile(filename, uid)
    assert file2 != file1
    assert file2.endswith("_new.txt")


def test_getpath_and_dictkey():
    """Test if the getpath method retrieves the correct file path using a dictkey."""
    cabinet = FilingCabinet("root", test_dir, "subj3")
    filename = "info.csv"
    uid="special"
    file_path = cabinet.newfile(filename, uid)
    assert cabinet.getpath("special") == file_path


def test_add_behavior():
    """Ensure that when "add" behavior selected, the file is created without a suffix and data is appended to end of file."""
    cabinet = FilingCabinet("root", test_dir, "subj5")

    filename = "data_add.csv"
    uid = "data"
    file = cabinet.newfile(filename, uid, behavior="add")

    # ensure that a unique file has NOT been created
    assert not file.endswith("_new.txt")

    # open file and write initial data
    with open(file, "w") as f:
        f.write("first line\n")

    # use FilingCabinet to append data
    file_add = cabinet.newfile(filename, uid, behavior="add")
    with open(file_add, "a") as f:
        f.write("second line\n")

    # ensure both lines are present
    with open(file, "r") as f:
        lines = f.readlines()

    assert lines == ["first line\n", "second line\n"]


def test_loadbackup_date_stripping():
    """
    Test whether the loadbackup method correctly strips the date from filenames.
    """
    # Create filename from info
    current_date = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMAT_LESS_SEC)
    subject = "TESTER"
    trialtype = "VICKREY"
    condition1 = "EPO"
    condition2 = ""
    suffix = "exothread_left"
    prefix = build_prefix(SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)
    filename = build_filename(FORMAT=FILENAME_FORMAT, PREFIX=prefix, DATE=current_date, SUFFIX=suffix, EXT="csv")

    cabinet = FilingCabinet(test_dir, "test_loadbackup_date_stripping")


    file_path = cabinet.newfile(filename, suffix)
    with open(file_path, "w") as f:
        f.write("Original file: " + current_date)

    new_cabinet = FilingCabinet(test_dir, "test_loadbackup_date_stripping")
    new_cabinet.loadbackup(prefix)

    assert new_cabinet.filepaths_dict[suffix] == file_path


    # loadbackup should return False if no matching files


def test_loadbackup_rules():
    """
    Test whether the latest and oldest files are correctly identified when multiple files exist.
    """


def teardown_module(module):
    shutil.rmtree(test_dir, ignore_errors=True)


