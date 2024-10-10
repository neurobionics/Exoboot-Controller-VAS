import random

class OccupancyMap:
    def __init__(self, nlines, ncols, signature):
        self.nlines = nlines
        self.ncols = ncols
        self.signature = signature

        self.layout = []

    def __repr__(self):
        fulltext = ""
        for l in range(self.nlines):
            fulltext += "".join(self.occupancies(l, 0, self.ncols - 1)) + "\n"
        return fulltext
    
    def clampl(self, l):
        return max(min(l, self.nlines - 1), 0)
    
    def clampc(self, c):
        return max(min(c, self.ncols - 1), 0)

    def cleanslate(self):
        self.layout = []
        for _ in range(self.nlines):
            self.layout.append([self.signature] * self.ncols)

    def resize(self, nlines, ncols):
        self.nlines = nlines
        self.ncols = ncols

    def getsignature(self, l, c):
        l = self.clampl(l)
        return self.layout[l][min(max(c, 0), self.ncols - 1)]

    def occupancies(self, l, c, n):
        l = self.clampl(l)
        return self.layout[l][max(0, c):min(n + c, self.ncols)]

    def occupy(self, l, c, occupancies):
        if l >= 0 and l < self.nlines:
            for i in range(max(0, c), min(len(occupancies) + c, self.ncols)):
                if self.layout[l][i] == self.signature:
                    self.layout[l][i] = occupancies[i - c]

class CharLayout:
    def __init__(self, nlines, ncols, signature, bgchar=" ", keepbottomborder=False):
        self.nlines = nlines
        self.ncols = ncols
        self.signature = signature
        self.bgchar = bgchar
        self.keepbottomborder = keepbottomborder

        self.layout = []
        self.occupancymap = OccupancyMap(self.nlines, self.ncols, self.signature)

    def __repr__(self):
        fulltext = ""
        for l in range(self.nlines):
            fulltext += "".join(self.readline(l)) + "\n"
        return fulltext

    def clampl(self, l):
        return max(min(l, self.nlines - 1), 0)
    
    def clampc(self, c):
        return max(min(c, self.ncols - 1), 0)

    def cleanslate(self):
        self.layout = []
        for _ in range(self.nlines):
            self.layout.append([self.bgchar] * self.ncols)
        self.occupancymap.cleanslate()

    def resize(self, nlines, ncols):
        self.nlines = nlines
        self.ncols = ncols
        self.occupancymap.resize(self.nlines, self.ncols)

    def insert(self, l, c, text):
        occupancies = self.occupancymap.occupancies(l, c, len(text))
        for i in range(max(0, c), min(len(text) + c, self.ncols)):
            if occupancies[i - max(0, c)] == self.occupancymap.signature:
                self.layout[l][i] = text[i - c]
    
    def insertsublayout(self, layout, l_o, c_o):
        for l in range(min(layout.nlines, self.nlines - l_o - int(self.keepbottomborder))):
            line = layout.readline(l)
            occupancy = layout.occupancies(l, 0, layout.ncols)
            self.insert(l + l_o, c_o, line)
            self.occupancymap.occupy(l + l_o, c_o, occupancy)

    def read(self, l, c, n):
        l = self.clampl(l)
        c = self.clampc(c)
        return self.layout[l][c:min(c+n, self.ncols)]
    
    def readline(self, l):
        l = self.clampl(l)
        return self.layout[l][0:self.ncols + 1]

    def getsignature(self, l, c):
        return self.occupancymap.getsignature(l, c)

    def occupancies(self, l, c, n):
        return self.occupancymap.occupancies(l, c, n)
    
    def occupy(self, l, c, occupancy):
        self.occupancymap.occupy(l, c, occupancy)
    
class Background(CharLayout):
    def __init__(self, nlines, ncols, signature, bgchar=" ", borderchar=" ", bordertype = "borderchar", keepbottomborder=False):
        super().__init__(nlines, ncols, signature, bgchar=bgchar, keepbottomborder=keepbottomborder)
        self.borderchar = borderchar
        self.bordertype = bordertype
        self.borderwidth = 1
        
    def getbc(self, l=0, c=0):
        match self.bordertype:
            case "none":
                return self.bgchar
            case "borderchar":
               return self.borderchar
            case "box":
                if l == 0:
                    if c == 0:
                        return '\U0000250f'
                    if c == self.ncols - 1:
                        return  '\U00002513'
                    return '\U00002501'
                elif l == self.nlines - 1:
                    if c == 0:
                        return '\U00002517'
                    elif c == self.ncols - 1:
                        return '\U0000251B'
                    return '\U00002501'
                else:
                    return '\U00002503'
            case "glitch":
                return chr(random.randint(32, 122))
            case "repeatedtext":
                pass
            case "textsnake":
                pass

    def getcleanlayout(self):
        cleanlayout = []
        match self.bordertype:
            case "none":
                for _ in range(self.nlines):
                    cleanlayout.append([self.bgchar] * self.ncols)
                return cleanlayout

            case "borderchar":
                edge = [self.borderchar] * self.ncols
                body = [self.bgchar] * (self.ncols - 2)
                body.insert(0, self.borderchar)
                body.append(self.borderchar)

                cleanlayout.append(edge.copy())
                for _ in range(self.nlines - 2):
                    cleanlayout.append(body.copy())
                cleanlayout.append(edge.copy())

                return cleanlayout

            case "box":
                cleanlayout.append([self.getbc(0, t) for t in range(self.ncols)])
                for s in range(self.nlines - 2):
                    body = [self.bgchar] * (self.ncols - 2)
                    body.insert(0, self.getbc(s + 1, 0))
                    body.append(self.getbc(s + 1, self.ncols - 1))
                    cleanlayout.append(body)
                cleanlayout.append([self.getbc(self.nlines - 1, b) for b in range(self.ncols)])

                return cleanlayout

            case "glitch":
                cleanlayout.append([self.getbc() for _ in range(self.ncols)])
                for _ in range(self.nlines - 2):
                    body = [self.bgchar] * (self.ncols - 2)
                    body.insert(0, self.getbc())
                    body.append(self.getbc())
                    cleanlayout.append(body)
                cleanlayout.append([self.getbc() for _ in range(self.ncols)])

                return cleanlayout

    def cleanslate(self):
        self.layout = self.getcleanlayout()
        self.occupancymap.cleanslate()
