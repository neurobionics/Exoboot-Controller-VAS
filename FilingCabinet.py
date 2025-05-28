import os, csv

from pathlib import Path
from collections import deque

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
        self.validfiletypes = ("csv", "txt")
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
        # TODO remove check or something
        try:
            assert type in self.validfiletypes
        except:
            print("{} not in validfiletypes")
            #TODO exit or raise error

        # Set default file name collision behavior
        if not behavior:
            behavior = self.defaultbehavior
        match behavior:
            case "new":
                filename = "{}.{}".format(name, type)

                # add _new until filename is unique
                isunique = False
                while not isunique:
                    if os.path.isfile(os.path.join(self.getparentfolderpath(), filename)):
                        filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                    else:
                        isunique = True
            case "add":
                # Append to existing file
                filename = "{}.{}".format(name, type)
            case _:
                Exception("FilingCabinet: not a valid behavior")

        # Create path to file
        fullpath = os.path.join(self.parentfolderpath, filename)

        # Use dictkey if specified otherwise use name as the key
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

    def loadbackup(self, file_prefix, rule=None):
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
                dictkey = file.split('.')[0]
                dictkey = dictkey.replace(os.path.join(self.getparentfolderpath(), file_prefix), "")
                dictkey = dictkey.replace("_new", "").strip('_')
                dictkeys.append(dictkey)
        dictkeys = set(dictkeys)

        # Find path to each unique dictkey
        for dictkey in dictkeys:
            subbackupfiles = [f for f in backupfiles if dictkey in f]

            if subbackupfiles:
                match rule:
                    case "newest":
                        subbackup = max(subbackupfiles, key=os.path.getctime)
                    case "oldest":
                        subbackup = max(subbackupfiles, key=os.path.getctime)
                    case _:
                        print("No rule implemented for case {}".format(rule))

                for snippet in subbackup.split(os.sep):
                    if snippet.endswith(self.validfiletypes):
                        subject_info = snippet.split('.')[0]
                        subject_info = subject_info.split('_')
                        dictkey = subject_info[4]

                        self._load(subbackup, dictkey)

        return True
    

if __name__ == "__main__":
    """
    FilingCabinet Demo
    """

    # Create FilingCabinet for subject "dummy"
    parentfolder = "testfolder"
    cabinet = FilingCabinet("a", "b", "c", "dummy")

    # Create txt files in subject_data and subject subfolder to show they exist
    Path(os.path.join(parentfolder, "asdf.txt")).touch()
    Path(os.path.join(cabinet.getparentfolderpath(), "qwer.txt")).touch()

    # Use FilingCabinet to create new file
    # Since qwer.txt exists, follow "new" behavior (add _new to filename)
    qwer_path = cabinet.newfile("qwer", "txt", behavior="new", dictkey="special_identifier")
    print("qwer filepath: {}".format(qwer_path))

    # Get qwer_file path using getpath
    # Should be same as qwer_path
    iforgotpath = cabinet.getpath("special_identifier")
    print("from getpath: {}".format(iforgotpath))

    # Create testcsv in subject subfolder
    with open(iforgotpath, 'a') as f:
        writer = csv.writer(f, lineterminator='\n',quotechar='|')
        writer.writerow(["foo", "bar"])

    print("Demo Finished")
