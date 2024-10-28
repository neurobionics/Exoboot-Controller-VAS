import os, csv, copy, threading
from typing import Type
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
    def __init__(self, subject):
        self.subject = subject
        self.subject_data_path = ""

        if not os.path.isdir("subject_data"):
            os.mkdir("subject_data")
        self.subject_data_path = os.path.join(self.subject_data_path, "subject_data")
        
        if not os.path.isdir(os.path.join(self.subject_data_path, self.subject)):
            os.mkdir(os.path.join(self.subject_data_path, self.subject))
        self.subject_data_path = os.path.join(self.subject_data_path, self.subject)

        self.filepaths_dict = {}
        self.validfiletypes = ["csv", "txt"]

        self.validbehaviors = ["new", "add"]
        self.defaultbehavior = "new"

    def get_subject_data_path(self):
        """
        Return path to folder in subject_data
        """
        return self.subject_data_path
    
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
                    if os.path.isfile(os.path.join(self.get_subject_data_path(), filename)):
                        filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                    else:
                        isunique = True
            case "add":
                # Use existing file
                filename = "{}.{}".format(name, type)
            case _:
                Exception("FilingCabinet: not a valid behavior")

        fullpath = os.path.join(self.subject_data_path, filename)

        # If no specified dictkey, put path in filepaths_dict under fullpath
        if not dictkey:
            self.filepaths_dict[name] = fullpath
        else:
            self.filepaths_dict[dictkey] = fullpath

        return fullpath

    def setnewfilebehavior(self, behavior):
        try:
            assert behavior in ["new", "add"]
            self.defaultbehavior = behavior
        except:
            print("FilingCabinet.setdefaultbehavior: not a valid behavior")

    def getpath(self, name):
        """
        Returns path from filepaths_dict
        """
        return self.filepaths_dict[name]


class LoggingNexus:
    def __init__(self, subjectID, file_prefix, filingcabinet, *threads, pause_event=Type[threading.Event]):
        self.subjectID = subjectID
        self.file_prefix = file_prefix
        self.pause_event = pause_event

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
        pathname = self.filingcabinet.getpath()
        for thread in self.thread_names:
            filename = self.filenames[thread]
            filepath = self.filingcabinet.newfile(filename, "csv", behavior="new")
            # filepath = os.path.join(pathname, filename)

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
            if self.pause_event.is_set():
                pathname = self.filingcabinet.getpath()
                for thread in self.thread_names:
                    filename = self.filenames[thread]
                    fullfilename = self.filingcabinet.newfile()
                    # fullfilename = os.path.join(pathname, filename)

                    fields = self.thread_fields[thread]
                    stash = self.thread_stashes[thread]
                    stash_size = len(stash)

                    with open(fullfilename, 'a') as f:
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
    cabinet = FilingCabinet("dummy")

    # Create txt files in subject_data and subject subfolder to show they exist
    Path(os.path.join("subject_data", "asdf.txt")).touch()
    Path(os.path.join(cabinet.get_subject_data_path(), "qwer.txt")).touch()

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

    print("Demo Finished\n")
