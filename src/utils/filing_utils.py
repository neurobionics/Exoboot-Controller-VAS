import argparse

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
    
    # set up argparser
    parser = argparse.ArgumentParser(description="VAS experimental type (10X/trial type/trial cond/desc/usebackup):")
    parser.add_argument("--sub", type=int, default=101, help="Subject ID (default: 101)", required=True)
    parser.add_argument("--trial-type", type=str, default=" acclimation", help="Trial Type (default: acclimation)", required=True)
    parser.add_argument("--trial-cond", type=str, help="Trial Condition", required=False)
    parser.add_argument("--desc", type=int, help="Description", required=False)
    parser.add_argument("--backup", type=bool, default=False, help="Use backup data? (default: False)", required=False)

    # parse arguments
    args = parser.parse_args()
   
    # set global params from given args
    SUBJECT_ID = "S"+str(args.sub)
    TRIAL_TYPE = args.trial_type if args.trial_type else None
    TRIAL_CONDITION = args.trial_cond if args.trial_cond else None
    DESCRIPTION = args.desc if args.desc else None
    USE_BACKUP = args.backup if args.backup else None
    
    # fashion the file name to log data
    if TRIAL_CONDITION is not None and DESCRIPTION is not None:
        file_name = f"{SUBJECT_ID}_{TRIAL_TYPE}_{TRIAL_CONDITION}_{DESCRIPTION}_exothread"
    elif TRIAL_CONDITION is not None:
        file_name = f"{SUBJECT_ID}_{TRIAL_TYPE}_{TRIAL_CONDITION}_exothread"
    elif DESCRIPTION is not None:
        file_name = f"{SUBJECT_ID}_{TRIAL_TYPE}_{DESCRIPTION}_exothread"
    else:
        file_name = f"{SUBJECT_ID}_{TRIAL_TYPE}_exothread"
    
    print(f"File name: {file_name}")
        
    return file_name, SUBJECT_ID, TRIAL_TYPE, TRIAL_CONDITION, DESCRIPTION, USE_BACKUP
    
def get_logging_info(use_input_flag)->str:
    """"Get the location of the log file and the file name 
    of the exo data given users inputs for a particular VAS experiment.
    
    Returns:
        str: The path to the log file.
        str: The name of the log file.
    """
    
    # get user inputs
    if use_input_flag:
        file_name, SUBJECT_ID, TRIAL_TYPE, TRIAL_CONDITION, DESCRIPTION, USE_BACKUP = get_user_inputs()
    else:
        file_name = "tracking_test"
    
    log_path = "./src/logs/"
    
    return log_path, file_name