import os, sys, threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "curses_HUD"))

from curses_HUD.hud_thread import HUDThread

class DumbMainWrapper:
    def __init__(self):
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.quit_event = threading.Event()
        self.quit_event.set()

        self.mynum = 0

    def __repr__(self):
        return "I am DMW: {}".format(self.mynum)

if __name__ == "__main__":
    dumbmainwrapper = DumbMainWrapper()
    hudthread = HUDThread(None, "exohud_layout.json", pause_event=dumbmainwrapper.pause_event, quit_event=dumbmainwrapper.quit_event)
    hudthread.start()
