import os, csv, copy, threading
from typing import Type
from collections import deque
from rtplot import client


class LoggingNexus:
    def __init__(self, file_prefix, *threads, pause_event=Type[threading.Event], ):
        self.file_prefix = file_prefix
        self.pause_event = pause_event

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

        # Write Headers to temp name
        for thread in self.thread_names:
            filename = self.filenames[thread]
            fields = self.thread_fields[thread]
            with open(filename, 'a') as f:
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
        return self.thread_stashes[threadname][-1][field]

    def log(self):
        """
        Empty data from thread_stashes and write to corresponding file
        """
        if self.pause_event.is_set():
            for threadname in self.thread_names:
                fields = self.thread_fields[threadname]
                stash = self.thread_stashes[threadname]
                stash_size = len(stash)
                with open(self.filenames[threadname], 'a') as f:
                    writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n',quotechar='|')
                    for _ in range(stash_size):
                        writer.writerow(stash.popleft())
