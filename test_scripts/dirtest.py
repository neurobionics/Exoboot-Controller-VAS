import os, csv
from pathlib import Path

class FilingCabinet:
    """
    Class to create subject_data folder and subject subfolders
    """
    def __init__(self, subject):
        self.subject = subject
        self.subject_path = ""

        if not os.path.isdir("subject_data"):
            os.mkdir("subject_data")
        self.subject_path = os.path.join(self.subject_path, "subject_data")
        
        if not os.path.isdir(os.path.join(self.subject_path, self.subject)):
            os.mkdir(os.path.join(self.subject_path, self.subject))
        self.subject_path = os.path.join(self.subject_path, self.subject)

        self.filepaths_dict = {}
        self.validfiletypes = ["csv", "txt"]

    def getpath(self):
        return self.subject_path
    
    def newfile(self, name, type, behavior="new"):
        try:
            assert type in self.validfiletypes
        except:
            print("{} not in validfiletypes")

        match behavior:
            case "new":
                filename = "{}.{}".format(name, type)

                isunique = False
                while not isunique:
                    if os.path.isfile(os.path.join(self.getpath(), filename)):
                        filename = "{}_new.{}".format(filename.split(sep=".")[0], type)
                    else:
                        isunique = True
            case "add":
                filename = "{}.{}".format(name, type)
            case _:
                Exception("FilingCabinet: not a valid behavior")

        return filename


if __name__ == "__main__":
    cabinet = FilingCabinet("dummy")

    # Create txt files in subject_data and subject subfolder
    Path(os.path.join("subject_data", "asdf.txt")).touch()
    Path(os.path.join(cabinet.getpath(), "qwer.txt")).touch()

    asdfnew = cabinet.newfile("qwer", "txt")

    # Create testcsv in subject subfolder
    with open(os.path.join(cabinet.getpath(), asdfnew), 'a') as f:
        writer = csv.writer(f, lineterminator='\n',quotechar='|')
        writer.writerow(["foo", "bar"])