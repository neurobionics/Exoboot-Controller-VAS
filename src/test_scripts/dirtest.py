import os, csv
from pathlib import Path

class subject_data_filing_cabinet:
    def __init__(self, subject):
        self.subject = subject
        self.subject_path = ""

        if not os.path.isdir("subject_data"):
            os.mkdir("subject_data")
        self.subject_path = os.path.join(self.subject_path, "subject_data")
        
        if not os.path.isdir(os.path.join(self.subject_path, self.subject)):
            os.mkdir(os.path.join(self.subject_path, self.subject))
        self.subject_path = os.path.join(self.subject_path, self.subject)

    def getpath(self):
        return self.subject_path



if __name__ == "__main__":
    cabinet = subject_data_filing_cabinet("dummy")

    # Create txt files in subject_data and subject subfolder
    Path(os.path.join("subject_data", "asdf.txt")).touch()
    Path(os.path.join(cabinet.getpath(), "qwer.txt")).touch()

    # Create testcsv in subject subfolder
    with open(os.path.join(cabinet.getpath(), "testcsv.csv"), 'a') as f:
        writer = csv.writer(f, lineterminator='\n',quotechar='|')
        writer.writerow(["foo", "bar"])