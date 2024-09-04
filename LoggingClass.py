import os, csv, copy, threading
from typing import Type
from collections import deque

class ImposterThread:
    """
    Entry point to LoggingNexus
    """
    def __init__(self, name='imposterthread', fields=['pitime']):
        self.loggingnexus = None
        self.name = name
        self.fields = fields

        self.data_dict = dict.fromkeys(self.fields)

    def log_to_nexus(self):
        self.loggingnexus.append(self.name, self.data_dict)


class LoggingNexus:
    def __init__(self, *threads, pause_event=Type[threading.Event], ):
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
            self.filenames[threadname] = 'TEMP_' + threadname + '.csv'

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
