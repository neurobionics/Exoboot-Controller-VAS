import os, csv, copy, threading
from typing import Type
from collections import deque
from rtplot import client 
from constants import RTPLOT_FIELDS

class ImposterThread:
    """
    Entry point to LoggingNexus
    # TODO DETERMINE REMOVAL
    """
    def __init__(self, name='imposterthread', fields=['pitime']):
        self.loggingnexus = None
        self.name = name
        self.fields = fields

        self.data_dict = dict.fromkeys(self.fields)

    def log_to_nexus(self):
        self.loggingnexus.append(self.name, self.data_dict)


class LoggingNexus:
    def __init__(self, file_prefix, *threads, pause_event=Type[threading.Event], ):
        self.file_prefix = file_prefix
        self.thread_names = []
        self.thread_fields = {}
        self.thread_stashes = {}
        self.filenames = {}
        
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
            self.filenames[threadname] = self.file_prefix + threadname + '.csv'
        
        self.rtplot_data_dict = {key: 0 for key in RTPLOT_FIELDS}

        # Write Headers to temp name
        for thread in self.thread_names:
            filename = self.filenames[thread]
            fields = self.thread_fields[thread]
            with open(filename, 'w') as f:
                writer = csv.writer(f, lineterminator='\n',quotechar='|')
                writer.writerow(fields)

    def append(self, threadname, data_dict):
        """
        Append data dict to stashes
        Needs to be a deepcopy
        """
        data = copy.deepcopy(data_dict)
        self.thread_stashes[threadname].append(data)
        
        # send client
        if 'exothread' in threadname:
            # Get side
            if 'left' in threadname:
                side = '_left'
            elif 'right' in threadname:
                side = '_right'
                
            #  Assign data from thread dict to rtplot data dict
            self.rtplot_data_dict['pitime'+side] = data['pitime']
            self.rtplot_data_dict['motor_current'+side] = data['motor_current']/1000
            self.rtplot_data_dict['batt_volt'+side] = data['battery_voltage']/1000
            self.rtplot_data_dict['case_temp'+side] = data['temperature']
            self.rtplot_data_dict['ankle_angle'+side] = data['ankle_angle']
                
            # Get data and send to rtplot client
            plot_data_array = [*self.rtplot_data_dict.values()]
            client.send_array(plot_data_array)

    def log(self):
        """
        Empty data from thread_stashes and write to corresponding file
        """
        for threadname in self.thread_names:
            fields = self.thread_fields[threadname]
            stash = self.thread_stashes[threadname]
            stash_size = len(stash)
            with open(self.filenames[threadname], 'a') as f:
                writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n',quotechar='|')
                for _ in range(stash_size):
                    writer.writerow(stash.popleft())
