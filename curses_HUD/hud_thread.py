import os, sys, json, time, inspect, threading
from typing import Type
import curses, curses.panel

import widget_base, button_funcs
from widget_base import HUD


class HUDWrapper:
    def __init__(self, mainwrapper, stdscr, mouseinterval=10):
        self.mainwrapper = mainwrapper
        curses.mouseinterval(mouseinterval)
        stdscr.clear()

        self.availablewidgets = {}
        self.availablefuncs = {}

    def loadHUD(self, layoutfile):
        f = open(os.path.join(os.path.dirname(__file__), layoutfile), mode="r")
        layout = json.load(f)

        settings = layout["settings"]
        self.debugmode = settings["debugmode"]

        for name, obj in inspect.getmembers(widget_base):
            if inspect.isclass(obj) and issubclass(obj, widget_base.Widget) and obj != widget_base.Widget:
                self.availablewidgets[name] = obj
                if self.debugmode:
                    print(name, obj)

        self.availablefuncs = {}
        for name, obj in inspect.getmembers(button_funcs):
            if inspect.isfunction(obj):
                self.availablefuncs[name] = obj(self.mainwrapper)
                if self.debugmode:
                    print(name, obj)

        hudinfo = layout["HUD"]
        self.hud = HUD(hudinfo["nlines"], hudinfo["ncols"], 0, 0, hudinfo["signature"], **hudinfo["kwargs"], debug=self.debugmode)
        self.hud.cleanslate()
        self.hud.widget_dict[hudinfo["signature"]] = self.hud
        
        parents_link_todo = {}
        for info in layout["widgets"].values():
            signature = info["signature"]

            converted_kwargs = {}
            for k, v in info["kwargs"].items():
                if k == "onpressfunc":
                    converted_kwargs[k] = self.availablefuncs[v]
                else:
                    converted_kwargs[k] = v

            newwidget = self.availablewidgets[info["widgettype"]](info["nlines"], info["ncols"], info["l"], info["c"], signature, **converted_kwargs)
            newwidget.cleanslate()
            self.hud.widget_dict[signature] = newwidget
            parents_link_todo[signature] = info["parent"]

        for childsignature, parentsignature in parents_link_todo.items():
            self.hud.widget_dict[parentsignature].addwidget(self.hud.widget_dict[childsignature])

    @property
    def isrunning(self):
        return self.hud.isrunning
    
    def cleanslate(self):
        self.hud.cleanslate()
        return self

    def draw(self):
        self.hud.draw()
        return self

    def get_input(self):
        self.hud.get_input()
        return self

    def refresh(self):
        self.hud.refresh()
        return self


class HUDThread(threading.Thread):
    def __init__(self, mainwrapper, layoutfile, name='hud', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        super().__init__(name=name)
        self.mainwrapper = mainwrapper
        self.layoutfile = layoutfile
        self.pause_event = pause_event
        self.quit_event = quit_event
        self.daemon = daemon

        # Initialize hudwrapper
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        try:
            curses.start_color()
        except:
            pass

        self.hudwrapper = HUDWrapper(self.mainwrapper, self.stdscr, mouseinterval=10)
        self.hudwrapper.loadHUD(self.layoutfile)

    @property
    def isrunning(self):
        return self.hudwrapper.isrunning

    def getwidget(self, signature):
        return self.hudwrapper.hud.widget_dict[signature]

    def run(self):
        try:
            while self.hudwrapper.isrunning and self.quit_event.is_set():
                self.hudwrapper.cleanslate()
                self.hudwrapper.draw()
                self.hudwrapper.get_input()
                self.hudwrapper.refresh()
                curses.napms(10)
        except:
            pass
        finally:
            self.stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

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
    try:
        dumbmainwrapper = DumbMainWrapper()

        hudthread = HUDThread(dumbmainwrapper, "exohud_layout.json", pause_event=dumbmainwrapper.pause_event, quit_event=dumbmainwrapper.quit_event)
        hudthread.start()

        somenum = 0

        while dumbmainwrapper.quit_event.is_set():
            print("main thread")
            print("isrunning: {}".format(hudthread.isrunning))
            print("pause event: {}\nquit event: {}".format(dumbmainwrapper.pause_event.is_set(), dumbmainwrapper.quit_event.is_set()))
            print()

            # Set text in hud from main
            try:
                hudthread.getwidget("t0").settextline(0, "{}".format(somenum))
                hudthread.getwidget("t0").cleanslate()
            except:
                pass
        
            somenum += 1
            dumbmainwrapper.mynum = somenum

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("DONE")
