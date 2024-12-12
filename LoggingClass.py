import os, csv, copy, threading
from typing import Type
from pathlib import Path
from collections import deque, defaultdict
# from rtplot import client


class FilingCabinet:
    """
    Class to create subject_data folder and subject subfolders
    Access file using dictkey, write headers automatically
    Write row or rows of data, 
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

        # Settings
        self.validbehaviors = ["new", "add"]
        self.validfiletypes = ("csv", "txt")
        self.backupexceptions = []

        # Internal states
        self.loadstatus = False

        self.filepaths_dict = {}

        try:
            assert defaultbehavior in self.validbehaviors
            self.defaultbehavior = defaultbehavior
        except:
            print("Invalid defaultbehavior for FilingCabinet")
            self.defaultbehavior = "new"

        # CSV writer additions
        self.csvheaders = defaultdict(lambda: None)

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
        Adds filepath into filepaths_dict
        Creates corresponding csv.writer
        """
        self.filepaths_dict[dictkey] = filepath

    def setheader(self, dictkey, header):
        """
        Save header for a given dictkey
        """
        self.csvheaders[dictkey] = header

    def set_backupexceptions(self, backupexceptions):
        """"
        Set strings to ignore when loading backups
        Use to ignore exothread/GSE logging files
        """
        self.backupexceptions = backupexceptions
    
    def newfile(self, name, type, behavior=None, dictkey=None, header=None):
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
                    # Appends "_new" until file is unique
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
        dkey = dictkey if dictkey else name
        self.filepaths_dict[dkey] = fullpath

        # CSV Additions
        if header:
            self.setheader(dkey, header)
        
        header = self.csvheaders[dkey]
        if header:
            self.writerow(dkey, header)

        return fullpath

    def loadbackup(self, trial_type, file_prefix, rule="newest"):
        """
        Find newest existing file with file_prefix
        returns bool for completion status
        """
        if not self.backupexceptions:
            print("WARNING: No backupexceptions set. Set before loading otherwise loadbackup() will most likely fail")
            print(self.backupexceptions)

        backupfiles = []
        pfolderpath = self.getpfolderpath()
        for file in os.listdir(pfolderpath):
            isloadexception = any(loadexc in file for loadexc in self.backupexceptions)
            if file_prefix in file and not isloadexception:
                backupfiles.append(os.path.join(pfolderpath, file))

        if not backupfiles:
            # Create new files
            match trial_type.upper():
                case 'VICKREY':
                    auctionname = "{}_{}".format(file_prefix, "auction")
                    self.newfile(auctionname, "csv", dictkey="auction", header=['t', 'subject_bid', 'user_win_flag', 'current_payout', 'total_winnings'])

                    # TODO add settings to not create this file on the GUI side
                    surveyname = "{}_{}".format(file_prefix, "survey")
                    self.newfile(surveyname, "csv", dictkey="survey", header=['t', 'enjoyment', 'rpe'])

                case 'VAS':
                    header = ['btn_option', 'trial', 'pres']
                    for i in range(4): # TODO remove constant 4
                        header.append('torque{}'.format(i))
                        header.append('mv{}'.format(i))

                    vasresultsname = "{}_{}".format(file_prefix, "vasresults")
                    self.newfile(vasresultsname, "csv", dictkey="vasresults", header=header)

                case 'JND':
                    comparisonname = "{}_{}".format(file_prefix, "comparison")
                    self.newfile(comparisonname, "csv", dictkey="comparison", header=['rep', 'pres', 'prop', 'T_ref', 'T_comp', 'truth', 'higher'])

                case 'PREF':
                    prefname = "{}_{}".format(file_prefix, "pref")
                    self.newfile(prefname, "csv", dictkey="pref", header=['pres', 'torque'])

                case 'THERMAL':
                    pass

            self.loadstatus = False
            return self.loadstatus

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

        self.loadstatus = True
        return self.loadstatus

    def writerow(self, dictkey, data, fields=None):
        """
        Write single row using csv
        Detects type of data (list or dict)
        """
        filepath = self.filepaths_dict[dictkey]
        match data:
            case list():
                csv.writer(open(filepath, 'a'), lineterminator='\n',quotechar='|').writerow(data)
            case dict():
                fields = fields if fields else data.keys()
                csv.DictWriter(open(filepath, 'a'), fieldnames=fields, lineterminator='\n',quotechar='|').writerow(data)
            case _:
                # TODO add other csv writers?
                raise TypeError("Invalid data to writerow")
            
    def writerowmulti(self, dictkey, datastash, fields=None):
        """
        Write rows in datalist using csv writer
        Detects type of data (list or dict)
        Don't mix types in datalist
        """
        filepath = self.filepaths_dict[dictkey]
        stashsize = len(datastash)
        fields = fields if fields else datastash[0].keys()
        if stashsize > 0:
            match datastash[0]:
                case list():
                    for _ in range(stashsize):
                        csv.writer(open(filepath, 'a'), lineterminator='\n',quotechar='|').writerow(datastash.popleft())
                case dict():
                    for _ in range(stashsize):
                        csv.DictWriter(open(filepath, 'a'), fieldnames=fields, lineterminator='\n',quotechar='|').writerow(datastash.popleft())
                case _:
                    # TODO add other csv writers?
                    raise TypeError("Invalid data to writerow")


class LoggingNexus:
    def __init__(self, subjectID, file_prefix, filingcabinet, *threads, log_event=Type[threading.Event]):
        self.subjectID = subjectID
        self.file_prefix = file_prefix
        self.log_event = log_event

        self.thread_names = []
        self.thread_fields = {}
        self.thread_stashes = {}
        self.filenames = {}
        
        self.filingcabinet = filingcabinet

        self.setup(threads)

    def setup(self, threads):
        """
        Add each thread to LoggingNexus dicts
        Threads append to deques using their name
        deques dumped periodically into csv files using FilingCabinet
        """
        for thread in threads:
            thread.loggingnexus = self

            threadname = thread.name
            self.thread_names.append(threadname)
            self.thread_fields[threadname] = thread.fields
            self.thread_stashes[threadname] = deque()
            self.filenames[threadname] = "{}_{}".format(self.file_prefix, threadname)

            # New file using FilingCabinet
            # self.filingcabinet.newfile(self.filenames[threadname], "csv", behavior="new", dictkey=threadname, header=self.thread_fields[threadname])

    def update_suffix(self, suffix, thread):
        """
        Create new file with same file_prefix, thread, new suffix
        Redirect thread logging to the new file
        Clear stashs
        """
        # Log leftovers and clear deques
        self.log()
        self.flush()

        # New csv logging destination
        self.filenames[thread] = "{}_{}_{}".format(self.file_prefix, thread, suffix)
        self.filingcabinet.newfile(self.filenames[thread], "csv", behavior="new", dictkey=thread, header=self.thread_fields[thread])

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
        Empty data from thread_stashes and write to corresponding file using FilingCabinet
        """
        try:
            if self.log_event.is_set():
                for thread in self.thread_names:
                    fields = self.thread_fields[thread]
                    stash = self.thread_stashes[thread]
                    self.filingcabinet.writerowmulti(thread, stash, fields=fields)
        except KeyError:
            pass
        except Exception as e:
            print("LoggingNexus.log() error: ", e)

    def flush(self):
        """
        Clear deques
        """
        for stash in self.thread_stashes.values():
            if stash:
                stash.clear()


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
    qwer_path = cabinet.newfile("qwer", "csv", behavior="new", dictkey="special_identifier")
    print("qwer filepath: {}".format(qwer_path))

    # Get qwer_file path using getpath
    # Should be same as qwer_path
    iforgotpath = cabinet.getpath("special_identifier")
    print("from getpath: {}".format(iforgotpath))

    # Create testcsv in subject subfolder
    with open(iforgotpath, 'a') as f:
        writer = csv.writer(f, lineterminator='\n',quotechar='|')
        writer.writerow(["foo", "bar"])

    # Write using FilingCabinet writerow
    cabinet.writerow("special_identifier", ["bas", "boo"])

    # Set special_identifier header
    cabinet.setheader("special_identifier", ["my", "header", "test", "header"])
    print("Header", cabinet.csvheaders["special_identifier"])

    # Assign new file to special_identifier
    cabinet.newfile("qwer2", "csv", dictkey="special_identifier")

    # Write data using writerow
    cabinet.writerow("special_identifier", ["boo", "halloween"])

    print("Demo Finished")
