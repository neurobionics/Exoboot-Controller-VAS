import re, datetime
from src.logger.filing_cabinet import FilingCabinet

from src.settings.constants import DETROIT_TIMEZONE, DATETIME_FORMATTER_LESS_SEC, VALID_FILE_EXTENSIONS, FORMATCODE_TO_REGEX

if __name__ == "__main__":
    """
    FilingCabinet Demo
    """

    # # Create FilingCabinet for subject "dummy"
    # cabinet = FilingCabinet("a", "b", "c", "dummy")
    # parentfolder = cabinet.getparentfolderpath()

    # # Create txt files in subject_data and subject subfolder to show they exist
    # Path(os.path.join(parentfolder, "asdf.txt")).touch()
    # Path(os.path.join(cabinet.getparentfolderpath(), "qwer.txt")).touch()

    # # Use FilingCabinet to create new file
    # # Since qwer.txt exists, follow "new" behavior (add _new to filename)
    # qwer_path = cabinet.newfile(
    #     "qwer", "txt", behavior="new", dictkey="special_identifier"
    # )
    # print("qwer filepath: {}".format(qwer_path))

    # # Get qwer_file path using getpath
    # # Should be same as qwer_path
    # iforgotpath = cabinet.getpath("special_identifier")
    # print("from getpath: {}".format(iforgotpath))

    # # Create testcsv in subject subfolder
    # with open(iforgotpath, "a") as f:
    #     writer = csv.writer(f, lineterminator="\n", quotechar="|")
    #     writer.writerow(["foo", "bar"])

    # print("Demo Finished")

    """
    CREATE FILE NAME
    """

    PREFIX_FORMATTER_GENERIC = r'%SUBJECT_%TRIALTYPE_%CONDITION1_%CONDITION2'
    print(f"PREFIX_FORMATTER_GENERIC: {PREFIX_FORMATTER_GENERIC}")

    current_date = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMATTER_LESS_SEC)
    subject = "TESTER"
    trialtype = "VICKREY"
    condition1 = "EPO"
    condition2 = ""

    def build_prefix(**kwargs):
        assert kwargs["SUBJECT"] and kwargs["TRIALTYPE"]

        # Organize non-None kwargs
        codes = [code for code in re.split(r'.?%', PREFIX_FORMATTER_GENERIC) if code]
        args = [kwargs[code] for code in codes if kwargs[code]]

        # Retrieve separators
        seps = PREFIX_FORMATTER_GENERIC
        for code in codes:
            seps = seps.replace(f"%{code}", "")

        # Create prefix and specific format string
        prefix = args[0]
        prefix_formatter = f"%{codes[0]}"
        for i in range(1, len(args)):
            prefix = prefix + seps[i-1] + args[i]
            prefix_formatter = prefix_formatter + seps[i-1] + f"%{codes[i]}"

        return prefix, prefix_formatter
        

    prefix, prefix_formatter = build_prefix(SUBJECT=subject, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)
    print(f"PREFIX: {prefix}")
    print(f"PREFIX_FORMATTER: {prefix_formatter}\n")


    FILENAME_FORMATTER = "%PREFIX_%DATE_%SUFFIX.%EXT"
    print(f"FILENAME_FORMATTER: {FILENAME_FORMATTER}")

    def build_filename(**kwargs):
        filename = FILENAME_FORMATTER
        for k, v in kwargs.items():
            filename = filename.replace(f"%{k}", v)
        return filename

    filename = build_filename(PREFIX= prefix, DATE=current_date, SUFFIX="exothread_left", EXT="csv")
    print(f"FILENAME: {filename}\n")


    """
    STRIP FILE NAMES
    """

    # Create necessary regexes
    def datetime_format_code_to_regex(formatter):
        for formatcode, regex in FORMATCODE_TO_REGEX.items():
            formatter = formatter.replace(formatcode, regex)
        return formatter
    
    date_regex = datetime_format_code_to_regex(DATETIME_FORMATTER_LESS_SEC)
    print(f"DATE_REGEX: {date_regex}")

    ext_regex = r'\.(' + "|".join(VALID_FILE_EXTENSIONS) + ')'
    print(f"EXT_REGEX: {ext_regex}")


    def group_files_by_uid(filenames, STATIC, VARIABLE=None):
        """
        Search filenames for STATIC identifier and VALID_FILE_EXTENSIONS, then remove VARIABLE regexes
        Sort files grouping by unique identifier (uid i.e. whatever is left over from removal process)
        Returns groups of filenames under the same uid
        """
        uid_grouped_files = {}
        for filename in filenames:
            originalname = filename
            if STATIC in filename and any(ext in filename for ext in VALID_FILE_EXTENSIONS):
                new_uid = True
                for uid in uid_grouped_files.keys():
                    if uid in filename:
                        uid_grouped_files[uid].append(originalname)
                        new_uid = False
                        continue

                if new_uid:
                    uid = re.sub(STATIC, '', filename)
                    for V in VARIABLE:
                        uid = re.sub(V, '', uid)

                    # Clean start/end non-alphanumeric characters of uid
                    clean_uid = re.sub(r'^[\W_]+|[\W_]+$', '', uid)

                    uid_grouped_files[clean_uid] = [originalname]

        return uid_grouped_files
    
    file_grabbag = ["2025_07_20_20_27_TESTER_VICKREY_EPO_2025_07_20_20_33_2025_07_20_20_33_2025_07_20_20_33_____exothread_left______.csv",
                    "2025_07_20_20_33_TESTER_VICKREY_EPO_2025_07_20_20_34_exothread_left.csv",
                    "TESTER_VICKREY_EPO_2025_07_20_20_35_exothread_left_2025_07_20_20_33.png",
                    "TESTER_VICKREY_NPO_2025_07_20_20_33_exothread_left.csv",
                    "TESTER_VICKREY_WNE_2025_07_20_20_33_exothread_left.csv",
                    "TESTER_VAS_EPO_2025_07_20_20_33_exothread_left.csv",
                    "TESTER_VICKREY_EPO_2025_07_20_20_33_exothread_right.csv",
                    "TESTER_VICKREY_EPO_3000_07_20_20_33_exothread_right.csv",
                    "OTHER_VICKREY_EPO_2025_07_20_20_33_exothread_left.csv",
                    ]

    unique_files = group_files_by_uid(file_grabbag, STATIC=prefix, VARIABLE=[date_regex, ext_regex])
    print(unique_files)