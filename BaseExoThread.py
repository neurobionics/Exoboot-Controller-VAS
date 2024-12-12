import os, sys, threading
import time
from typing import Type
from abc import ABC, abstractmethod

class BaseThread(ABC, threading.Thread):
    """
    Base Thread class for any Exoboot threads. 

    Features:
        1) set daemon as an argument when initializing class
        2) pause and quit threading.Event for pausing thread and quitting thread

    Thread Loop Structure:
        1) on_pre_run runs once before entering while loop
        2) on_pre_pause runs before thread is paused
        3) iterate runs when thread is not paused
    
    When inheriting from this class, just change on_pre_pause and iterate methods
    
    Multiple threads share pause_event and quit_events. Events are set outside of the thread.

    Threads cannot lock out other threads from running
    """
    
    def __init__(self, name='Base', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        super().__init__(name=name)
        self.pause_event = pause_event
        self.quit_event = quit_event
        self.daemon = daemon

    @abstractmethod
    def on_pre_run(self):
        """Fill Out Yourself!!!"""
        pass
    
    @abstractmethod    
    def pre_iterate(self):
        """Fill Out Yourself!!!"""
        pass

    def on_pre_pause(self):
        """Fill Out Yourself!!!"""
        pass

    def iterate(self):
        """Fill Out Yourself!!!"""
        pass

    def post_iterate(self):
        """Fill Out Yourself!!!"""
        pass

    def on_pre_exit(self):
        """Fill Out Yourself!!!"""
        pass

    def run(self):
        """
        Generic Run with Pausing Capabilities

        Fill out on_pre_run(), pre_iterate(), on_pre_pause(), iterate(), post_iterate(), and on_pre_exit()
        """
        self.on_pre_run()
        try:
            while self.quit_event.is_set():
                self.pre_iterate()
                if not self.pause_event.is_set():
                    self.on_pre_pause()
                    self.pause_event.wait()
                self.iterate()
                self.post_iterate()
            self.on_pre_exit()
            
        except Exception as e:
            print("Exception: ", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


if __name__ == "__main__":
    class DemoThread(BaseThread):
        """
        Example how to inherit from BaseThread
        
        """
        def __init__(self, pause_event, quit_event, name='Demo'):
            super().__init__(name=name, pause_event=pause_event, quit_event=quit_event)

        def on_pre_run(self):
            print("Pre run: ", self.name)
            time.sleep(0.5)

        def on_pre_pause(self):
            print("Pre Pause ", self.name)

        def on_pre_exit(self):
            print("Pre Exit: ", self.name)

        def iterate(self):
            print("Doing stuff ", self.name)
            time.sleep(0.5)
            pass

    """Pause Event Demo"""

    # Set quit and pause events
    quit_event = threading.Event()
    quit_event.set()
    pause_event = threading.Event()
    pause_event.set()

    # Create threads with same quit and pause events to control at the same time
    t1 = DemoThread(pause_event=pause_event, quit_event=quit_event, name="t1")
    t2 = DemoThread(pause_event=pause_event, quit_event=quit_event, name="t2")

    # Start the inherited run() method
    t1.start()
    t2.start()

    # Demonstrate synchronized pausing using the pause_event
    try:
        while True:
            # Alternate beween 1.0 s of paused and unpaused threads
            time.sleep(1.0)
            pause_event.clear()
            time.sleep(1.0)
            pause_event.set()
    except KeyboardInterrupt:
        # Set pause_event to immediatly exit the pausing statement
        pause_event.set()

        # Clear quit_event to exit the main loop and run on_pre_exit() routine
        quit_event.clear()

        # Let threads finish their sleep() methods for proper exit (not needed if no sleep())
        time.sleep(1.0)
        print("Demo Finished")
