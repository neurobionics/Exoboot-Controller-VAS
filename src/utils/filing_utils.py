import argparse
import sys

def get_user_inputs()->str:
    """
    Get user inputs for the VAS experiment type and other parameters.
    Returns:
        str: The name of the file containing all data.
        str: The subject ID.
        str: The trial type.
        str: The trial condition.
        str: The trial description. Usually the date in this format: MMDDYY (i.e. 01312025, which is Jan 31, 2025)
        bool: Whether to use backup data or not.

    """
    try:
        # set up argparser
        parser = argparse.ArgumentParser(description="VAS experimental type (opt:tester/10X/trial type/opt:trial cond/opt:desc/opt:usebackup):")
        parser.add_argument("--sub-type", type=str, help="optional: Subject Type (ex: tester)", required=False)
        parser.add_argument("--sub-num", type=str, help="Subject ID (ex: 10X)", required=True)
        parser.add_argument("--trial-type", type=str, default=" acclimation", help="Trial Type (ex: acclimation)", required=True)
        parser.add_argument("--trial-cond", type=str, help="optional: Trial Condition", required=False)
        parser.add_argument("--desc", type=int, help="optional: Description", required=False)
        parser.add_argument("--backup", type=bool, default=False, help="optional: Use backup data? (default: False)", required=False)

        # parse arguments
        args = parser.parse_args()

        # set global params from given args
        SUBJECT_TYPE = args.sub_type if args.sub_type else None
        SUBJECT_ID = "S"+args.sub_num if args.sub_num else None
        TRIAL_TYPE = args.trial_type if args.trial_type else None
        TRIAL_CONDITION = args.trial_cond if args.trial_cond else None
        DESCRIPTION = args.desc if args.desc else None
        USE_BACKUP = args.backup if args.backup else None

        # fashion the file name to log data
        components = [SUBJECT_TYPE, SUBJECT_ID, TRIAL_TYPE, TRIAL_CONDITION, DESCRIPTION]
        file_name = "_".join(map(str, filter(None, components))) + "_exothread" # remove the None values & join

        print(f"File name: {file_name}")

        return file_name, SUBJECT_ID, TRIAL_TYPE, TRIAL_CONDITION, DESCRIPTION, USE_BACKUP

    except argparse.ArgumentError as err:
        (f"Argparsing error: {err}")
        sys.exit(1)

def get_logging_info(user_input_flag)->str:
    """"Get the location of the log file and the file name
    of the exo data given users inputs for a particular VAS experiment.

    Args:
        user_input_flag (bool): If True, prompts the user for inputs.
                                If False, uses a default file name.

    Returns:
        str: The path to the log file.
        str: The name of the log file.
    """

    # get user inputs
    if user_input_flag:
        file_name, SUBJECT_ID, TRIAL_TYPE, TRIAL_CONDITION, DESCRIPTION, USE_BACKUP = get_user_inputs()
    else:
        file_name = "tracking_test"

    log_path = "./src/logs/"

    return log_path, file_name