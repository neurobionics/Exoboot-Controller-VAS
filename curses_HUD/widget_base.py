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

    def draw(self, l_mouse, c_mouse):
        if self.isvisible:
            self.layout.cleanslate()
            if self.children:
                for widget in self.children:
                    widget.draw(l_mouse, c_mouse)
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

    def draw(self, l_mouse, c_mouse):
        if self.isvisible:
            self.cleanslate()
            self.parent.layout.insertsublayout(self.layout, self.l, self.c)

class Button(TextBox):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", textlines=[], onpressfunc=None, requires_top=True):
        super().__init__(nlines, ncols, l, c, signature, bgchar=bgchar, textlines=textlines)
        self.onpressfunc = onpressfunc
        self.requires_top = requires_top

    def onpress(self, **kwargs):
        if (self.is_top or not self.requires_top) and self.onpressfunc and kwargs["bstate"] & curses.BUTTON1_PRESSED:
            self.onpressfunc(self, **kwargs)
        if not self.is_top:
            self.lift(self.signature)

        self.parent.onpress(**kwargs)

class ToggleButton(Button):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", textlines=[], onpressfunc=None, requires_top=True, togglestate=False):
        super().__init__(nlines, ncols, l, c, signature, bgchar=bgchar, textlines=textlines, onpressfunc=onpressfunc, requires_top=requires_top)
        self.togglestate = togglestate

    def onpress(self, **kwargs):
        if self.is_top or not self.requires_top:
            if self.onpressfunc and kwargs["bstate"] & curses.BUTTON1_PRESSED:
                self.onpressfunc(self, togglestate=self.togglestate, **kwargs)
                self.togglestate = not self.togglestate
        if not self.is_top:
            self.lift(self.signature)

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

    def draw(self, l_mouse, c_mouse):
        if self.dragstate:
            self.l = l_mouse + self.anchor[0] - self.absl + self.l
            self.c = c_mouse + self.anchor[1] - self.absc + self.c

            self.l = max(min(self.l, self.parent.layout.nlines - 1), 0)
            self.c = max(min(self.c, self.parent.layout.ncols - 1), -self.layout.ncols + 1)

        elif self.resizestate:
            nlines = max(l_mouse - self.absl , 2)
            ncols = max(c_mouse - self.absc, 2)
            self.layout.resize(nlines, ncols)

        self.layout.cleanslate()
        if self.children:
            for widget in self.children:
                widget.draw(l_mouse, c_mouse)
        self.parent.layout.insertsublayout(self.layout, self.l, self.c)

class HUD(Window):
    def __init__(self, nlines, ncols, l, c, signature, bgchar=" ", borderchar=" ", bordertype="borderchar", debug=False):
        super().__init__(nlines, ncols, 0, 0, signature, bgchar=bgchar, borderchar=borderchar, bordertype=bordertype, keepbottomborder=True)
        self.nlines = nlines
        self.ncols = ncols
        self.debug = debug

        self.widget_dict = {}
        self.running = True

        # Main Window
        self.win = curses.newwin(self.nlines + 1, self.ncols, 0, 0)
        self.win.keypad(1)
        self.win.nodelay(1)
        self.win.timeout(0)

        self.l_mouse = 0
        self.c_mouse = 0
        self.bstate = 0

        self.kb_text = ""
        self.mouse_text = ""

        self.current_widget = None

    @property
    def isrunning(self):
        return self.running

    def get_input(self):
        event = self.win.getch()
        if event == curses.KEY_MOUSE:
            _, self.c_mouse, self.l_mouse, _, self.bstate = curses.getmouse()
            self.mouse_text = str(self.bstate) + '_'+ str(curses.BUTTON1_PRESSED)
            if self.bstate & curses.BUTTON1_PRESSED and self.current_widget == None:
                signature = self.layout.getsignature(self.l_mouse, self.c_mouse)
                self.current_widget = self.widget_dict[signature]
                self.current_widget.onpress(bstate=self.bstate, l=self.l_mouse, c=self.c_mouse)
            elif self.bstate & curses.BUTTON1_RELEASED and self.current_widget:
                self.current_widget.onpress(bstate=self.bstate, l=self.l_mouse, c=self.c_mouse)
                self.current_widget = None
            else:
                pass

        elif event >= 0:
            if event == ord('Q'):
                self.running = False
            else:
                self.kb_text = event

    def draw(self):
        self.layout.cleanslate()

        for widget in self.children:
            widget.draw(self.l_mouse, self.c_mouse)

        if self.debug:
            self.layout.insert(self.nlines - 1, 1, "({}, {})".format(self.c_mouse, self.l_mouse))
            self.layout.insert(self.nlines - 1, 15, "SIGN: {}".format(self.layout.occupancymap.occupancies(min(self.l_mouse, self.nlines - 1), min(self.c_mouse, self.ncols - 1), 1)))
            self.layout.insert(self.nlines - 1, 30, "KBIN: {}".format(self.kb_text))
            self.layout.insert(self.nlines - 1, 37, "MSIN:" + str(self.mouse_text))

        # Draw to window
        self.win.clear()
        for l in range(self.nlines):
            self.win.addstr("".join(self.layout.readline(l)), curses.color_pair(1))

    def refresh(self):
        # self.win.refresh()
        self.win.noutrefresh()
        curses.doupdate()
