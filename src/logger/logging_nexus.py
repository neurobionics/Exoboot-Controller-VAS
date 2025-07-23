import os, csv, copy, threading
from typing import Type
from pathlib import Path
from collections import deque
# from rtplot import client
from src.logger.filing_cabinet_regex import build_filename

class LoggingNexus:
    def __init__(self, prefix, date, filingcabinet, *threads):
        self.prefix = prefix
        self.date = date

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

            self.thread_names.append(thread.name)
            self.thread_fields[thread.name] = thread.fields
            self.thread_stashes[thread.name] = deque()

            filename = build_filename(PREFIX=self.prefix, DATE=self.date, SUFFIX=thread.name, EXT="csv")
            self.filenames[thread.name] = filename

            filepath = self.filingcabinet.newfile(filename, uid=thread.name, behavior="new")
            with open(filepath, 'a') as f:
                writer = csv.writer(f, lineterminator='\n',quotechar='|')
                writer.writerow(thread.fields)

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
            return {}

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