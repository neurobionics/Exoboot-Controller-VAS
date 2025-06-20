import csv
import src.GUI_communication.exoboot_remote_pb2 as pb2
import src.GUI_communication.exoboot_remote_pb2_grpc as pb2_grpc

class ExobootCommServicer(pb2_grpc.exoboot_over_networkServicer):
    """
    Communication between anything and pi

    This class is rpi side
    """

    def __init__(self, mainwrapper, filingcabinet, quit_event, session_details):
        super().__init__()
        self.mainwrapper = mainwrapper
        self.session_details = session_details
        self.filingcabinet = filingcabinet

        self.startstamp = session_details.START_STAMP
        self.usebackup = session_details.USE_BACKUP
        self.file_prefix = session_details.FILENAME
        self.quit_event = quit_event

        # file set-up
        self.file_setup()


    def file_setup(self):
        # Load backup or...
        loadstatus = False
        if self.usebackup:
            loadstatus = self.filingcabinet.loadbackup(self.file_prefix, rule="newest")

        # ... create new files
        if not loadstatus:
            if self.session_details.TRIAL_TYPE.upper() == 'VICKREY':
                auctionname = "{}_{}".format(self.file_prefix, "auction")
                auctionpath = self.filingcabinet.newfile(auctionname, "csv", dictkey="auction")

                surveyname = "{}_{}".format(self.file_prefix, "survey")
                surveypath = self.filingcabinet.newfile(surveyname, "csv", dictkey="survey")

                with open(auctionpath, 'a', newline='') as f:
                    csv.writer(f).writerow(['t', 'subject_bid', 'user_win_flag', 'current_payout', 'total_winnings'])
                with open(surveypath, 'a', newline='') as f:
                    csv.writer(f).writerow(['t', 'enjoyment', 'rpe'])

            elif self.session_details.TRIAL_TYPE.upper() == 'VAS':
                vasresultsname = "{}_{}".format(self.file_prefix, "vasresults")
                vasresultspath = self.filingcabinet.newfile(vasresultsname, "csv", dictkey="vasresults")

                with open(vasresultspath, 'a', newline='') as f:
                    header = ['btn_option', 'trial', 'pres']
                    for i in range(20): # TODO remove constant 20
                        header.append('torque{}'.format(i))
                        header.append('mv{}'.format(i))
                    csv.writer(f).writerow(header)

            elif self.session_details.TRIAL_TYPE.upper() == 'JND':
                comparisonname = "{}_{}".format(self.file_prefix, "comparison")
                comparisonpath = self.filingcabinet.newfile(comparisonname, "csv", dictkey="comparison")

                # LEGACY TODO: Add extra logging on pi here for kaernbach (check file_prefix for trial cond)
                with open(comparisonpath, 'a', newline='') as f:
                    csv.writer(f).writerow(['pres', 'prop', 'T_ref', 'T_comp', 'truth', 'higher'])

            elif self.session_details.TRIAL_TYPE.upper() == 'PREF':
                prefname = "{}_{}".format(self.file_prefix, "pref")
                prefpath = self.filingcabinet.newfile(prefname, "csv", dictkey="pref")

                with open(prefpath, 'a', newline='') as f:
                    csv.writer(f).writerow(['pres', 'torque'])

            elif self.session_details.TRIAL_TYPE.upper() == 'THERMAL':
                pass


    # General Methods
    def testconnection(self, request, context):
        print("Testing Connection: {}".format(request.msg))
        self.subject_name = request.msg
        return pb2.receipt(received=True)

    def get_subject_info(self, nullmsg, context):
        return pb2.subject_info(startstamp=self.session_details.START_STAMP,
                                subjectID=self.session_details.SUBJECT_ID,
                                trial_type=self.session_details.TRIAL_TYPE,
                                trial_cond=self.session_details.TRIAL_CONDITION,
                                description=self.session_details.DESCRIPTION,
                                usebackup=self.session_details.USE_BACKUP)

    def chop(self, beaver, context):
        """
        Kill rpi from Client
        """
        self.quit_event.set()
        return pb2.receipt(received=True)

    # Exoboot Controller Commands
    def set_quit(self, quit_msg, context):
        """
        Exoboot_Thread Command
        Set quit event
        """
        quit = quit_msg.mybool
        print("QUIT COMMAND: {}".format(quit))
        if quit:
            self.mainwrapper.quit_event.clear()
        else:
            self.mainwrapper.quit_event.set()
        return pb2.receipt(received=True)

    def set_pause(self, pause_msg, context):
        """
        Exoboot_Thread Command
        Set pause event
        """
        pause = pause_msg.mybool
        print("PAUSE COMMAND: {}".format(pause))
        if pause:
            self.mainwrapper.pause_event.clear()
        else:
            self.mainwrapper.pause_event.set()
        return pb2.receipt(received=True)

    def set_log(self, log_msg, context):
        """
        Exoboot_Thread Command
        Set log event
        """
        log = log_msg.mybool
        print("LOG COMMAND: {}".format(log))
        if log:
            self.mainwrapper.log_event.clear()
        else:
            self.mainwrapper.log_event.set()
        return pb2.receipt(received=True)

    def set_torque(self, torque_msg, context):
        """
        Exoboot_Thread Command
        Sets peak torque of exoboots
        """
        # Printing out the request from the client
        peak_torque_left  = torque_msg.peak_torque_left
        peak_torque_right = torque_msg.peak_torque_right

        # TODO: Set torques in GSE ~ this is the peak torque sent by GUI
        # TODO: add in zmq/queue to send to main thread here
        self.mainwrapper.torque_setpoint(peak_torque_right)

        return pb2.receipt(received=True)

    def getpack(self, req_log, context):
        """
        Get value from LoggingNexus
        """
        thread = req_log.thread
        field = req_log.field
        val = self.mainwrapper.loggingnexus.get(thread, field)

        return pb2.ret_val(val=val)

    # Vickrey Auction Specific
    def call(self, resultmsg, context):
        t = resultmsg.t
        subject_bid = resultmsg.subject_bid
        user_win_flag = resultmsg.user_win_flag
        current_payout = resultmsg.current_payout
        total_winnings = resultmsg.total_winnings

        print("Received auction results: {}, {}, {}, {}, {}".format(t, subject_bid, user_win_flag, current_payout, total_winnings))
        datalist = [t, subject_bid, user_win_flag, current_payout, total_winnings]

        auctionpath = self.filingcabinet.getpath("auction")
        with open(auctionpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)

    def question(self, surveymsg, context):
        t = surveymsg.t
        enjoyment = surveymsg.enjoyment
        rpe = surveymsg.rpe

        print("Received survey results: {}, {}, {}".format(t, enjoyment, rpe))
        datalist = [t, enjoyment, rpe]

        surveypath = self.filingcabinet.getpath("survey")
        with open(surveypath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)

    # VAS Specific
    def update_vas_info(self, vasinfomsg, context):
        """
        Start overtime logging in a new file
        """
        btn_num = int(vasinfomsg.btn_num)
        trial = int(vasinfomsg.trial)
        pres = int(vasinfomsg.pres)

        print("Received updated vas info: ", btn_num, trial, pres)
        overtimename = "{}_overtime_B{}_T{}_P{}".format(self.file_prefix, btn_num, trial, pres)
        overtimepath = self.filingcabinet.newfile(overtimename, "csv", dictkey="overtime")

        header = ['pitime']
        for i in range(btn_num):
            header.append("Torque{}".format(i))
            header.append("MV{}".format(i))

        with open(overtimepath, 'a', newline='') as f:
            csv.writer(f).writerow(header)

        return pb2.receipt(received=True)

    def slider_update(self, slidermsg, context):
        """
        Send updated slider info
        """
        pitime = slidermsg.pitime
        torques = slidermsg.torques
        mvs = slidermsg.mvs

        datalist = [pitime]
        for torque, mv in zip(torques, mvs):
            datalist.append(torque)
            datalist.append(mv)

        overtimepath = self.filingcabinet.getpath("overtime")
        with open(overtimepath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)

    def presentation_result(self, presmsg, context):
        """
        Send updated slider info
        """
        btn_option = int(presmsg.btn_option)
        trial = int(presmsg.trial)
        pres = int(presmsg.pres)
        torques = presmsg.torques
        values = presmsg.values

        print("Received presentation results: {}, {}, {}, {}, {}".format(btn_option, trial, pres, torques, values))
        datalist = [btn_option, trial, pres]
        for t, mv in zip(torques, values):
            datalist.append(t)
            datalist.append(mv)

        vasresultspath = self.filingcabinet.getpath("vasresults")
        with open(vasresultspath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)

    # JND Specific
    def comparison_result(self, compmsg, context):
        pres = compmsg.pres
        prop = compmsg.prop
        T_ref = compmsg.T_ref
        T_comp = compmsg.T_comp
        truth = compmsg.truth
        answer = compmsg.answer

        print("Received comparison results: {}, {}, {}, {}, {}, {}".format(pres, prop, T_ref, T_comp, truth, answer))
        datalist = [pres, prop, T_ref, T_comp, truth, answer]

        comparisonpath = self.filingcabinet.getpath("comparison")
        with open(comparisonpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)

    # LEGACY TODO: add in custom grpc msg
    def comparison_result_stair(self, compmsg, context):
        pres = compmsg.pres
        prop = compmsg.prop
        T_ref = compmsg.T_ref
        T_comp = compmsg.T_comp
        truth = compmsg.truth
        answer = compmsg.answer

        print("Received comparison results: {}, {}, {}, {}, {}, {}".format(pres, prop, T_ref, T_comp, truth, answer))
        datalist = [pres, prop, T_ref, T_comp, truth, answer]   # LEGACY TODO: change data list to include stair info

        comparisonpath = self.filingcabinet.getpath("comparison")
        with open(comparisonpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)

    # Pref Specific
    def pref_result(self, prefmsg, context):
        pres = prefmsg.pres
        torque = prefmsg.torque

        print("Received preference results: {}, {}".format(pres, torque))
        datalist = [pres, torque]

        prefpath = self.filingcabinet.getpath("pref")
        with open(prefpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)
