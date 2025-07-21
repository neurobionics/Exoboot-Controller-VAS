import os, csv, re

from pathlib import Path
from collections import deque

from src.settings.constants import VALID_FILE_EXTENSIONS


class FilingCabinet:
    """
    Class to create subject_data folder and subject subfolders

    Keeps track of subject in subject_data

    Resolves conflicting file names

    Return paths using filepaths_dict lookup
    """

    def __init__(self, *hierarchy, defaultbehavior="new"):
        self._init_folder_hierarchy(self, *hierarchy)

        self.filepaths_dict = {}
        self.validfiletypes = VALID_FILE_EXTENSIONS
        self.validbehaviors = ["new", "add"]
        try:
            assert defaultbehavior in self.validbehaviors
            self.defaultbehavior = defaultbehavior
        except:
            print("Invalid defaultbehavior for FilingCabinet")
            self.defaultbehavior = "new"

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

    def newfile(self, name, type, behavior=None, dictkey=None):
        """
        Create path for new file in subject_data_path folder
        Resolves conflicting names using behavior

        Store paths under dictkey
        """

        try:
            assert type in self.validfiletypes
        except:
            print("{} not in validfiletypes")

        if not behavior:
            behavior = self.defaultbehavior

        if behavior == "new":
            # Create new file
            filename = "{}.{}".format(name, type)

            isunique = False
            while not isunique:
                if os.path.isfile(os.path.join(self.getparentfolderpath(), filename)):
                    filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                else:
                    isunique = True
        elif behavior == "add":
            # Use existing file
            filename = "{}.{}".format(name, type)
        else:
            Exception("FilingCabinet: not a valid behavior")

        fullpath = os.path.join(self.parentfolderpath, filename)

        # If no specified dictkey, put path in filepaths_dict under fullpath
        if not dictkey:
            self.filepaths_dict[name] = fullpath
        else:
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
        dictkeys = []
        for file in backupfiles:
            if file.endswith(self.validfiletypes):
                dictkey = file.split(".")[0]
                dictkey = dictkey.replace(
                    os.path.join(self.getparentfolderpath(), file_prefix), ""
                )
                dictkey = dictkey.replace("_new", "").strip("_")

                # TODO: remove datetime if it exists in the filename (i.e. "2025_MM_DD_HH_")
                pattern = re.compile(r"\d{4}(.*)_")
                result = pattern.search(dictkey)
                date = dictkey[result.span()[0]:result.span()[1]-1]
                dictkey = dictkey.replace(date, "").strip("_")
                dictkeys.append(dictkey)

        dictkeys = set(dictkeys)

        # Find path to each unique dictkey
        for dictkey in dictkeys:
            subbackupfiles = [f for f in backupfiles if dictkey in f]

            if subbackupfiles:
                if rule == "newest":
                    subbackup = max(subbackupfiles, key=os.path.getctime)
                elif rule == "oldest":
                    subbackup = min(subbackupfiles, key=os.path.getctime)
                else:
                    print("No rule implemented for case {}".format(rule))
                    break

                self._load(subbackup, dictkey)

        return True
