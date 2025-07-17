import os
import shutil
import pytest
from pathlib import Path
from src.logger.filing_cabinet import FilingCabinet

test_dir = "test_subject_data"


def setup_module(module):
    os.makedirs(test_dir, exist_ok=True)


def teardown_module(module):
    shutil.rmtree(test_dir, ignore_errors=True)


def test_folder_hierarchy_creation():
    """Test if the FilingCabinet creates the folder hierarchy correctly."""
    cabinet = FilingCabinet("root", test_dir, "subj1")
    assert os.path.isdir(cabinet.getparentfolderpath())


def test_newfile_creates_unique_file():
    """Test if a unique file is created when the same name is used to create a file.
    Ensures that the new file has a "-new" suffix at the end to prevent conflicts."""
    cabinet = FilingCabinet("root", test_dir, "subj2")
    file1 = cabinet.newfile("data", "txt")
    Path(file1).touch()
    file2 = cabinet.newfile("data", "txt")
    assert file2 != file1
    assert file2.endswith("_new.txt")


def test_getpath_and_dictkey():
    """Test if the getpath method retrieves the correct file path using a dictkey."""
    cabinet = FilingCabinet("root", test_dir, "subj3")
    file_path = cabinet.newfile("info", "csv", dictkey="special")
    assert cabinet.getpath("special") == file_path


def test_add_behavior():
    """Ensure that when "add" behavior selected, the file is created without a suffix and data is appended to end of file."""
    cabinet = FilingCabinet("root", test_dir, "subj5", defaultbehavior="add")
    file = cabinet.newfile("data", "txt")

    # ensure that a unique file has NOT been created
    assert not file.endswith("_new.txt")

    # open file and write initial data
    with open(file, "w") as f:
        f.write("first line\n")

    # use FilingCabinet to append data
    file_add = cabinet.newfile("data", "txt", behavior="add")
    with open(file_add, "a") as f:
        f.write("second line\n")

    # ensure both lines are present
    with open(file, "r") as f:
        lines = f.readlines()

    assert lines == ["first line\n", "second line\n"]


def test_load_and_loadbackup():
    """
    Test the _load and loadbackup methods of FilingCabinet.
    This test verifies that:
    - The _load method correctly adds an existing file path to the filepaths_dict and can be retrieved with getpath.
    - The loadbackup method returns False when no files matching the given prefix exist in the folder.
    - (TODO) Future: Ensure that datetime in filenames does not interfere with backup loading logic.
    """
    cabinet = FilingCabinet("root", test_dir, "subj6")
    file_path = cabinet.newfile("backup", "csv", dictkey="bk")
    Path(file_path).touch()
    cabinet._load(file_path, "bk2")
    assert cabinet.getpath("bk2") == file_path

    # loadbackup should return False if no matching files
    assert not cabinet.loadbackup("notfoundprefix")
