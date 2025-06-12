from constants import TRIAL_CONDS_DICT

class Validator:
    def __init__(self, subjectID, trial_type, trial_cond, description, usebackup):
         # Subject info
        self.subjectID = subjectID
        self.trial_type = trial_type.upper()
        self.trial_cond = trial_cond.upper()
        self.description = description
        self.usebackup = usebackup in ["true", "True", "1", "yes", "Yes"]
        self.file_prefix = "{}_{}_{}_{}".format(self.subjectID, self.trial_type, self.trial_cond, self.description)

        # Validate subject info against TRIAL_CONDS_DICT
        if self.trial_type not in TRIAL_CONDS_DICT.keys():
            raise Exception("Invalid trial_type\nSee TRIAL_CONDS_DICT for accepted parameters\n")
        valid_conds = TRIAL_CONDS_DICT[self.trial_type]["COND"]
        if valid_conds and self.trial_cond not in valid_conds:
            raise Exception("Invalid trial_cond\nSee TRIAL_CONDS_DICT for accepted parameters\n")
        valid_descs = TRIAL_CONDS_DICT[self.trial_type]["DESC"]
        if valid_descs and self.description.upper() not in valid_descs:
            raise Exception("Invalid description\nSee TRIAL_CONDS_DICT for accepted parameters\n")

if __name__ == "__main__":
    """
    Test Validator
    Try every combination of trials, conds, descs
    Print only successes
    """
    trials = ["Vickrey", "VAS", "JND", "PREF", "BOO", "APPLE"]
    conds = ["WNE", "EPO", "NPO", "SPLITLEG", "SAMELEG", "SLIDER", "BUTTON", "DIAL", "FOOD", "EXO", "FOO"]
    descs = ["UNIFORM", "STAIR", "ESCALATOR"]

    successbool = False
    for t in trials:
        for c in conds:
            for d in descs:
                try:
                    Validator("VALIDATOR", t, c, d, "yes")
                    successbool = True
                except Exception:
                    successbool = False

                if successbool:
                    print("{}: {}".format("{}_{}_{}".format(t, c, d), successbool))
