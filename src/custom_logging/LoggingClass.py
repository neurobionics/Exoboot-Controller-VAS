import os
import csv
import copy
from pathlib import Path
from collections import deque
# from rtplot import client


class FilingCabinet:
    """
    Class to create subject_data folder and subject subfolders

    Keeps track of subject in subject_data
    
    Resolves conflicting file names

    Return paths using filepaths_dict lookup
    """
    def __init__(self, pfolder, subject, defaultbehavior="new"):
        self.subject = subject
        self.pfolderpath = ""

        if not os.path.isdir(pfolder):
            os.mkdir(pfolder)
        self.pfolderpath = os.path.join(self.pfolderpath, pfolder)
        
        if not os.path.isdir(os.path.join(self.pfolderpath, self.subject)):
            os.mkdir(os.path.join(self.pfolderpath, self.subject))
        self.pfolderpath = os.path.join(self.pfolderpath, self.subject)

        self.filepaths_dict = {}
        self.validfiletypes = ("csv", "txt")

        self.validbehaviors = ["new", "add"]
        try:
            assert defaultbehavior in self.validbehaviors
            self.defaultbehavior = defaultbehavior
        except:
            print("Invalid defaultbehavior for FilingCabinet")
            self.defaultbehavior = "new"

    def getpfolderpath(self):
        """
        Return path to folder in subject_data
        """
        return self.pfolderpath

    def getpath(self, name):
        """
        Returns path from filepaths_dict
        """
        return self.filepaths_dict[name]
    
    def load(self, filepath, dictkey):
        """
        Adds existing filepath into filepaths_dict
        MUST ALREADY EXIST
        """
        self.filepaths_dict[dictkey] = filepath
    
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

        match behavior:
            case "new":
                # Create new file
                filename = "{}.{}".format(name, type)

                isunique = False
                while not isunique:
                    if os.path.isfile(os.path.join(self.getpfolderpath(), filename)):
                        filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                    else:
                        isunique = True
            case "add":
                # Use existing file
                filename = "{}.{}".format(name, type)
            case _:
                Exception("FilingCabinet: not a valid behavior")

        fullpath = os.path.join(self.pfolderpath, filename)

        # If no specified dictkey, put path in filepaths_dict under fullpath
        if not dictkey:
            self.filepaths_dict[name] = fullpath
        else:
            self.filepaths_dict[dictkey] = fullpath

        return fullpath

    def loadbackup(self, file_prefix, rule=None):
        backupfiles = []
        pfolderpath = self.getpfolderpath()
        for file in os.listdir(pfolderpath):
            if file_prefix in file:
                backupfiles.append(os.path.join(pfolderpath, file))

        if not backupfiles:
            return False

        # find unique dictkeys
        dictkeys = []
        for file in backupfiles:
            if file.endswith(self.validfiletypes):
                dictkey = file.split('.')[0]
                dictkey = dictkey.replace(os.path.join(self.getpfolderpath(), file_prefix), "")
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

                        self.load(subbackup, dictkey)

        return True

class LoggingNexus:
    def __init__(self, subjectID, file_prefix, filingcabinet, *threads):
        self.subjectID = subjectID
        self.file_prefix = file_prefix

        self.thread_names = []
        self.thread_fields = {}
        self.thread_stashes = {}
        self.filenames = {}
        
        self.filingcabinet = filingcabinet

        self.setup(threads)

    def setup(self, threads):
        """
        Add each thread to LoggingNexus dicts
        Threads log to deques using their name
        """
        for thread in threads:
            thread.loggingnexus = self

            threadname = thread.name
            self.thread_names.append(threadname)
            self.thread_fields[threadname] = thread.fields
            self.thread_stashes[threadname] = deque()
            self.filenames[threadname] = "{}_{}".format(self.file_prefix, threadname)

        # Write Headers to temp name
        for thread in self.thread_names:
            filename = self.filenames[thread]
            filepath = self.filingcabinet.newfile(filename, "csv", behavior="new", dictkey=thread)
            fields = self.thread_fields[thread]

            with open(filepath, 'a') as f:
                writer = csv.writer(f, lineterminator='\n',quotechar='|')
                writer.writerow(fields)

    def append(self, threadname, data_dict):
        """
        Append data dict to stashes
        Needs to be a deepcopy
        """
        data = copy.deepcopy(data_dict)
        self.thread_stashes[threadname].append(data)
        
        # # send client
        # if 'exothread_' in threadname:
        #     if 'left' in threadname:
        #         # pull data from dictionary
        #         self.rtplot_data_dict['pitime_left'] = data['pitime']
        #         self.rtplot_data_dict['motor_current_left'] = data['motor_current']
        #         self.rtplot_data_dict['batt_volt_left'] = data['battery_voltage']
        #         self.rtplot_data_dict['case_temp_left'] = data['temperature']
                
        #         plot_data_array = [self.rtplot_data_dict.values()]
        #     else:
        #         self.rtplot_data_dict['pitime_right'] = data['pitime']
        #         self.rtplot_data_dict['motor_current_right'] = data['motor_current']
        #         self.rtplot_data_dict['batt_volt_right'] = data['battery_voltage']
        #         self.rtplot_data_dict['case_temp_right'] = data['temperature']
                
        #         plot_data_array = [self.rtplot_data_dict.values()]
            
        #     client.send_array(plot_data_array)

    def get(self, threadname, field):
        try:
            data = self.thread_stashes[threadname][-1][field]
            return data
        except:
            return -1

    def log(self):
        """
        Empty data from thread_stashes and write to corresponding file
        """
        try:
            for thread in self.thread_names:
                filename = self.filingcabinet.getpath(thread)
                fields = self.thread_fields[thread]
                stash = self.thread_stashes[thread]
                stash_size = len(stash)

                with open(filename, 'a') as f:
                    writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n',quotechar='|')
                    for _ in range(stash_size):
                        writer.writerow(stash.popleft())
        except Exception as e:
            print("LoggingNexus.log() error: ", e)


if __name__ == "__main__":
    """
    FilingCabinet Demo
    """

    # Create FilingCabinet for subject "dummy"
    pfolder = "testfolder"
    cabinet = FilingCabinet(pfolder, "dummy")

    # Create txt files in subject_data and subject subfolder to show they exist
    Path(os.path.join(pfolder, "asdf.txt")).touch()
    Path(os.path.join(cabinet.getpfolderpath(), "qwer.txt")).touch()

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
