def btn0func(mainwrapper, **kwargs):
    def func(self, mainwrapper=mainwrapper, **kwargs):
        self.layout.bgchar = chr((ord(self.layout.bgchar) + 1))
        self.layout.cleanslate()
    return func

def setpauseevent(mainwrapper, **kwargs):
    def func(self, mainwrapper=mainwrapper, **kwargs):
        if not kwargs["togglestate"]:
            mainwrapper.pause_event.clear()
        else:
            mainwrapper.pause_event.set()
    return func

def setquitevent(mainwrapper, **kwargs):
    def func(self, mainwrapper=mainwrapper, **kwargs):
        if not kwargs["togglestate"]:
            mainwrapper.quit_event.clear()
        else:
            mainwrapper.quit_event.set()
    return func
