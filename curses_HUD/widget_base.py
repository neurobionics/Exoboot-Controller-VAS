import curses
from layout_base import CharLayout, Background

class Widget:
    def __init__(self, l, c, signature, bgchar=" "):
        self.signature = signature
        self.l = l
        self.c = c
        self.bgchar = bgchar

        self.layout = None

        self.parent = None
        self.children = None

        self.isvisible = True

    @property
    def absl(self):
        if self.parent:
            parentl = self.parent.absl
        else:
            parentl = self.l
        return self.l + parentl
    
    @property
    def absc(self):
        if self.parent:
            parentc = self.parent.absc
        else:
            parentc = self.c
        return self.c + parentc

    @property
    def is_top(self):
        if self.parent:
            return self.parent.children[0] == self and self.parent.is_top
        else:
            return True
        
    def assignparent(self, parent):
        self.parent = parent

    def addwidget(self, widget):
        self.children.append(widget)
        widget.assignparent(self)

    def lift(self, signature):
        if self.children:
            for i, widget in enumerate(self.children):
                if widget.signature == signature:
                    self.children.insert(0, self.children.pop(i))
                    break
        if self.parent:
            self.parent.lift(self.signature)

    def draw(self):
        if self.isvisible:
            self.layout.cleanslate()
            if self.children:
                for widget in self.children:
                    widget.draw()
            self.parent.layout.insertsublayout(self.layout, self.l, self.c)

class TextBox(Widget):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", textlines=[], useprefix=False, lineprefix=[]):
        super().__init__(l, c, signature, bgchar=bgchar)
        self.textlines = textlines
        self.useprefix = useprefix
        self.lineprefix = lineprefix

        if not self.textlines:
            self.textlines = [""] * nlines
        else:
            self.textlines = textlines

        if self.useprefix and not self.lineprefix:
            self.textlines = [""] * nlines

        self.layout = CharLayout(nlines, ncols, self.signature, bgchar=self.bgchar)

    def cleanslate(self):
        self.layout.cleanslate()
        for l in range(self.layout.nlines):
            text = self.textlines[l]
            if self.useprefix:
                text = self.lineprefix[l] + text
            self.layout.insert(l, 0, text)
        return self

    def inserttext(self, l, text):
        """Overwrite contents"""
        self.layout.insert(l, 0, text)

    def setprefix(self, l, text):
        """Set prefix for line l"""
        self.lineprefix[l] = text

    def settextline(self, l, text):
        """Set textline at l"""
        self.textlines[l] = text

    def onpress(self, **kwargs):
        self.parent.onpress(**kwargs)

    def draw(self):
        if self.isvisible:
            self.parent.layout.insertsublayout(self.layout, self.l, self.c)

class Button(TextBox):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", textlines=[], onpressfunc=None):
        super().__init__(nlines, ncols, l, c, signature, bgchar=bgchar, textlines=textlines)
        self.onpressfunc = onpressfunc

    def onpress(self, **kwargs):
        if not self.is_top:
            self.lift(self.signature)
        if self.onpressfunc:
            self.onpressfunc(self, **kwargs)

        self.parent.onpress(**kwargs)

class ToggleButton(Button):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", textlines=[], onpressfunc=None, togglestate=None):
        super().__init__(nlines, ncols, l, c, signature, bgchar=bgchar, textlines=textlines, onpressfunc=onpressfunc)
        self.togglestate = togglestate

    def onpress(self, **kwargs):
        if not self.is_top:
            self.lift(self.signature)
        elif self.onpressfunc and kwargs["bstate"] & curses.BUTTON1_PRESSED:
            self.onpressfunc(self, togglestate=self.togglestate, **kwargs)
            self.togglestate = not self.togglestate

        self.parent.onpress(**kwargs)

class Window(Widget):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", borderchar=" ", bordertype="borderchar", isdragable=False, isresizeable=False, keepbottomborder=False):
        super().__init__(l, c, signature, bgchar=bgchar)
        self.layout = Background(nlines, ncols, self.signature, bgchar=bgchar, borderchar=borderchar, bordertype=bordertype, keepbottomborder=keepbottomborder)
        
        self.anchor = [0, 0]
        self.isdragable = isdragable
        self.dragstate = False

        self.isresizeable = isresizeable
        self.resizestate = False

        self.children = []

    def cleanslate(self):
        self.layout.cleanslate()
        return self

    def ontopborder(self, l):
        return l == 0
    
    def onbotrightcorner(self, l, c):
        return l == self.layout.nlines - 1 and c == self.layout.ncols - 1

    def onpress(self, **kwargs):
        if self.parent and not self.is_top:
            self.parent.lift(self.signature)

        if kwargs["bstate"] & curses.BUTTON1_PRESSED:
            l_rel = kwargs["l"] - self.absl
            c_rel = kwargs["c"] - self.absc
            if self.isdragable and self.ontopborder(l_rel):
                self.dragstate = True
                self.anchor = [-l_rel, -c_rel]
            elif self.isresizeable and self.onbotrightcorner(l_rel, c_rel):
                self.resizestate = True

        elif kwargs["bstate"] & curses.BUTTON1_RELEASED:
            self.dragstate = False
            self.resizestate = False

    def draw(self):
        if self.dragstate:
            _, c_mouse, l_mouse, _, _ = curses.getmouse()
            self.l = l_mouse + self.anchor[0] - self.absl + self.l
            self.c = c_mouse + self.anchor[1] - self.absc + self.c

            self.l = max(min(self.l, self.parent.layout.nlines - 1), 0)
            self.c = max(min(self.c, self.parent.layout.ncols - 1), -self.layout.ncols + 1)

        elif self.resizestate:
            _, c_mouse, l_mouse, _, _ = curses.getmouse()
            nlines = max(l_mouse - self.absl , 2)
            ncols = max(c_mouse - self.absc, 2)
            self.layout.resize(nlines, ncols)

        self.layout.cleanslate()
        if self.children:
            for widget in self.children:
                widget.draw()
        self.parent.layout.insertsublayout(self.layout, self.l, self.c)

class HUD(Window):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", borderchar=" ", bordertype="borderchar", debug=False):
        super().__init__(nlines, ncols, 0, 0, signature, bgchar=bgchar, borderchar=borderchar, bordertype=bordertype, keepbottomborder=True)
        self.nlines = nlines
        self.ncols = ncols
        self.debug = debug

        self.widget_dict = {}
        self.running = True

        # Mouse inputs
        self.win = curses.newwin(self.nlines + 1, self.ncols, 0, 0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        self.win.keypad(True)
        self.win.nodelay(True)
        print('\033[?1003h')

        self.kb_text = ""
        self.mouse_text = ""

        self.current_widget = None

    @property
    def isrunning(self):
        return self.running

    def get_input(self):
        event = self.win.getch()
        if event == curses.KEY_MOUSE:
            _, c, l, _, bstate = curses.getmouse()
            self.mouse_text = str(bstate)
            if bstate & curses.BUTTON1_PRESSED:
                signature = self.layout.getsignature(l, c)
                self.current_widget = self.widget_dict[signature]
                self.current_widget.onpress(bstate=bstate, l=l, c=c)
            elif bstate & curses.BUTTON1_RELEASED and self.current_widget:
                self.current_widget.onpress(bstate=bstate, l=l, c=c)
                self.current_widget = None

        elif event >= 0:
            if event == ord('Q'):
                self.running = False
            else:
                self.kb_text = event

    def draw(self):
        self.layout.cleanslate()

        for widget in self.children:
            widget.draw()

        if self.debug:
            _, x, y, _, btn = curses.getmouse()
            self.layout.insert(self.nlines - 1, 1, "({}, {})".format(x, y))
            self.layout.insert(self.nlines - 1, 15, "SIGN: {}".format(self.layout.occupancymap.occupancies(min(y, self.nlines - 1), min(x, self.ncols - 1), 1)))
            self.layout.insert(self.nlines - 1, 30, "KBIN: {}".format(self.kb_text))
            self.layout.insert(self.nlines - 1, self.ncols-15, "MSIN:" + str(self.mouse_text))

        # Draw to window
        self.win.clear()
        for l in range(self.nlines):
            self.win.addstr("".join(self.layout.readline(l)))

    def refresh(self):
        # self.win.refresh()
        self.win.noutrefresh()
        curses.doupdate()


# TODO add curses chgat to change color of textboxes
