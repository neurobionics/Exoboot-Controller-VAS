import os, csv, re

from pathlib import Path
from collections import deque
from src.logger.filing_cabinet_regex import group_files_by_uid, datetime_formatcode_to_regex, file_extension_regex

from src.settings.constants import VALID_FILE_EXTENSIONS, DATETIME_FORMAT_LESS_SEC


class FilingCabinet:
    """
    Class to create subject_data folder and subject subfolders

    Keeps track of subject in subject_data

    Resolves conflicting file names

    Return paths using filepaths_dict lookup
    """

    def __init__(self, *hierarchy):
        self._init_folder_hierarchy(self, *hierarchy)

        self.filepaths_dict = {}
        self.validfiletypes = VALID_FILE_EXTENSIONS
        self.validbehaviors = ["new", "add"]

    def _init_folder_hierarchy(self, *hierarchy):
        """
        Initialize folders form hierarchy
        Creates folders if necessary
        """
        self.parentfolderpath = os.path.join(*hierarchy[1:])
        os.makedirs(self.parentfolderpath, exist_ok=True)
        return

    def getparentfolderpath(self):
        """
        Return path to folder in subject_data
        """
        return self.parentfolderpath

    def getpath(self, name):
        """
        Returns path from filepaths_dict
        """
        return self.filepaths_dict[name]

    def newfile(self, filename, dictkey, behavior="new"):
        """
        Create path for new file in subject_data_path folder
        Resolves conflicting names using behavior

        Store paths under dictkey
        """
        if behavior == "new":
            # Create new file
            isunique = False
            while not isunique:
                if os.path.isfile(os.path.join(self.getparentfolderpath(), filename)):
                    filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                else:
                    isunique = True
        elif behavior == "add":
            pass
        else:
            Exception("FilingCabinet: not a valid behavior")

        fullpath = os.path.join(self.parentfolderpath, filename)

        # If no specified dictkey, put path in filepaths_dict under fullpath
        self.filepaths_dict[dictkey] = fullpath

        return fullpath

    def _load(self, filepath, dictkey):
        """
        Adds existing filepath into filepaths_dict
        MUST ALREADY EXIST
        """
        self.filepaths_dict[dictkey] = filepath

    def loadbackup(self, file_prefix, rule="newest"):
        """
        Load hierarchy from existing
        """

        parentfolderpath = self.getparentfolderpath()

        # Load any files with file_prefix in it
        backupfiles = []
        for file in os.listdir(parentfolderpath):
            if file_prefix in file:
                backupfiles.append(os.path.join(parentfolderpath, file))

        if not backupfiles:
            return False

        # Find unique dictkeys
        date_regex = datetime_formatcode_to_regex(DATETIME_FORMAT_LESS_SEC)
        ext_regex = file_extension_regex(VALID_FILE_EXTENSIONS)
        files_by_uid = group_files_by_uid(backupfiles, STATIC=file_prefix, VARIABLE=[date_regex, ext_regex])

        # Find path to each unique dictkey
        for uid, files in files_by_uid.items():
            if rule == "newest":
                subbackup = max(files, key=os.path.getctime)
            elif rule == "oldest":
                subbackup = min(files, key=os.path.getctime)
            else:
                print("No rule implemented for case {}".format(rule))
                return False

            self._load(subbackup, uid)

        return True
