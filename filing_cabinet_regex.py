import re, datetime
from src.logger.filing_cabinet import FilingCabinet

from src.settings.constants import DETROIT_TIMEZONE, DATETIME_FORMAT_LESS_SEC, VALID_FILE_EXTENSIONS, FORMATCODE_TO_REGEX, PREFIX_FORMAT_GENERIC, FILENAME_FORMAT


def build_prefix(prefix_format=PREFIX_FORMAT_GENERIC, **kwargs):
    """
    Build prefix using PREFIX_FORMAT_GENERIC as guidelines
    Minimal requirements of SUBJECT and TRIALTYPE
    Omits CONDITION# if empty
    """
    assert kwargs["SUBJECT"] and kwargs["TRIALTYPE"]

    codes = re.findall(r'%([^\W_]*)', prefix_format)

    vals = []
    seps = []
    for code in codes:
        if code in kwargs:
            val = kwargs[code]
            if val:
                vals.append(val)
                sep = re.search(f'([\W_]*)(?=%{code})', prefix_format)
                seps.append(sep.group(0) if sep else "")

    # Create prefix and specific format string
    prefix = ""
    for sep, val in zip(seps, vals):
        prefix = prefix + sep + val

    return prefix

def build_filename(format=FILENAME_FORMAT, **kwargs):
    """
    Build filename using FORMAT and supplied kwargs
    """
    codes = re.findall(r'%([^\W_]*)', format)

    filename = kwargs["FORMAT"]
    for code in codes:
        assert kwargs[code]
        for k, v in kwargs.items():
            filename = filename.replace(f"%{k}", v)
    return filename

def datetime_formatcode_to_regex(format_):
    """
    Convert Datetime format code string to regex
    """
    for formatcode, regex in FORMATCODE_TO_REGEX.items():
        format_ = format_.replace(formatcode, regex)
    return format_
    
def file_extension_regex(ext=VALID_FILE_EXTENSIONS):
    """
    Convert file extensions list to regex
    """
    return r'\.(' + "|".join(ext) + ')'

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


if __name__ == "__main__":
    """
    DEMO creating prefix and filename
    """
    current_date = datetime.datetime.now(tz=DETROIT_TIMEZONE).strftime(DATETIME_FORMAT_LESS_SEC)
    subject = "TESTER"
    trialtype = "VICKREY"
    condition1 = "EPO"
    condition2 = ""

    print(f"PREFIX_FORMAT_GENERIC: {PREFIX_FORMAT_GENERIC}")

    prefix = build_prefix(SUBJECT=subject, PREFIX=prefix, TRIALTYPE=trialtype, CONDITION1=condition1, CONDITION2=condition2)
    print(f"PREFIX: {prefix}")


    print(f"FILENAME_FORMAT: {FILENAME_FORMAT}")

    filename = build_filename(FORMAT=FILENAME_FORMAT, DATE=current_date, SUFFIX="exothread_left", EXT="csv")
    print(f"FILENAME: {filename}\n")



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

    date_regex = datetime_formatcode_to_regex(DATETIME_FORMAT_LESS_SEC)
    ext_regex = file_extension_regex(VALID_FILE_EXTENSIONS)
    print(f"DATE_REGEX: {date_regex}")
    print(f"EXT_REGEX: {ext_regex}")

    unique_files = group_files_by_uid(file_grabbag, STATIC=prefix, VARIABLE=[date_regex, ext_regex])
    print("FILES BY UID: ", unique_files)
