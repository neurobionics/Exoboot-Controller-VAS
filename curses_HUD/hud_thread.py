import os, sys, json, time, inspect, random, threading
from typing import Type
import curses, curses.panel

sys.path.insert(0, os.path.dirname(__file__))

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
        # Load widget and button funcs
        for name, obj in inspect.getmembers(widget_base):
            if inspect.isclass(obj) and issubclass(obj, widget_base.Widget) and obj != widget_base.Widget:
                self.availablewidgets[name] = obj
                # if self.debugmode:
                #     print(name, obj)

        self.availablefuncs = {}
        for name, obj in inspect.getmembers(button_funcs):
            if inspect.isfunction(obj):
                self.availablefuncs[name] = obj(self.mainwrapper)
                # if self.debugmode:
                #     print(name, obj)

        # Open layout file (.json)
        f = open(os.path.join(os.path.dirname(__file__), layoutfile), mode="r")
        hudinfo = json.load(f)

        settings = hudinfo["settings"]
        stylesheet = hudinfo["stylesheet"]
        layout = hudinfo["layout"]
        
        # Load settings
        self.debugmode = settings["debugmode"]

        # Build HUD widget
        hudwidget = layout["HUD"]
        self.hud = HUD(hudwidget["nlines"], hudwidget["ncols"], 0, 0, hudwidget["signature"], **hudwidget["kwargs"], debug=self.debugmode)
        self.hud.cleanslate()
        self.hud.widget_dict[hudwidget["signature"]] = self.hud

        # Initialize colors
        color_name_to_num = {}
        colornum = 16
        for color_name, info in stylesheet["colors"].items():
            curses.init_color(colornum, info["rgb"][0], info["rgb"][1], info["rgb"][2])
            color_name_to_num[color_name] = colornum
            colornum += 1

        # Create color pairs
        # Reserved pairnums: 0 as terminal default, 1 as hud default
        self.hud.colorpairs = {0: 0}
        colorpairname = hudwidget["colorpair"]
        fg = color_name_to_num.get(stylesheet["colorpairs"][colorpairname]["colorpair"][0], stylesheet["colorpairs"][colorpairname]["colorpair"][0])
        bg = color_name_to_num.get(stylesheet["colorpairs"][colorpairname]["colorpair"][1], stylesheet["colorpairs"][colorpairname]["colorpair"][1])
        curses.init_pair(1, fg, bg)

        colorpair_num = 2
        for pairname, pairinfo in stylesheet["colorpairs"].items():
            fg = color_name_to_num.get(pairinfo["colorpair"][0], pairinfo["colorpair"][0])
            bg = color_name_to_num.get(pairinfo["colorpair"][1], pairinfo["colorpair"][1])
            curses.init_pair(colorpair_num, fg, bg)
            self.hud.colorpairs[pairname] = colorpair_num
            colorpair_num += 1
        print(self.hud.colorpairs)

        # Build other widgets
        parents_link_todo = {}
        for widget in layout["widgets"].values():
            signature = widget["signature"]
            colorpair = widget.get("colorpair", 1)

            # Convert kwargs to funcs
            converted_kwargs = {"colorpair": colorpair}
            for k, v in widget["kwargs"].items():
                if k == "onpressfunc":
                    converted_kwargs[k] = self.availablefuncs[v]
                else:
                    converted_kwargs[k] = v

            newwidget = self.availablewidgets[widget["widgettype"]](widget["nlines"], widget["ncols"], widget["l"], widget["c"], signature, **converted_kwargs)
            newwidget.cleanslate()
            self.hud.widget_dict[signature] = newwidget
            parents_link_todo[signature] = widget["parent"]

        # Link widgets to parents
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

        # Setup for inputs
        curses.curs_set(0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS|curses.REPORT_MOUSE_POSITION) # Must include REPORT_MOUSE_POSITION
        print('\033[?1002h') # https://stackoverflow.com/questions/56300134/how-to-enable-mouse-movement-events-in-curses/64809709#64809709

        curses.start_color()
        curses.use_default_colors()

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
        except Exception as e:
            print("Exception: ", e)
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

            try:
                hudthread.getwidget("si").settextline(0, "dummy, foo, bar, qwert")

                exostate_text = "Running" if dumbmainwrapper.pause_event.is_set() else "Paused"
                hudthread.getwidget("ls").settextline(0, exostate_text)
                hudthread.getwidget("rs").settextline(0, exostate_text)
                hudthread.getwidget("lpt").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("rpt").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("lct").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("rct").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("lcs").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("rcs").settextline(0, chr(random.randint(36, 160)))

                hudthread.getwidget("batv").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("bati").settextline(0, chr(random.randint(36, 160)))

                hudthread.getwidget("bert").settextline(0, chr(random.randint(36, 160)))
                hudthread.getwidget("vicon").settextline(0, chr(random.randint(36, 160)))
            except:
                pass
        
            somenum += 1
            dumbmainwrapper.mynum = somenum

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("DONE")

# TODO
#   1) add animation/sequence class for defining time series of frames for a textbox
#   2) create better button
