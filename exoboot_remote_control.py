import os, sys, csv, time, grpc, datetime, threading
from typing import Type
from concurrent import futures

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import exoboot_remote.exoboot_remote_pb2 as pb2
import exoboot_remote.exoboot_remote_pb2_grpc as pb2_grpc
from shared_files.BaseExoThread import BaseThread


class ExobootRemoteClient:
    """
    Client running on network
    """
    def __init__(self, server_IP):
        self.channel = grpc.insecure_channel(server_IP)
        self.stub = pb2_grpc.exoboot_over_networkStub(self.channel)
        self.startstamp = 0

# General Methods    
    def testconnection(self, guiname='none'):
        """
        Sends test message to LoggingServer
        """
        msg = pb2.testmsg(msg="Hello from {}".format(guiname))
        response = self.stub.testconnection(msg)
        if response:
            print("Connection Successful\n")
        else:
            raise ConnectionError("AuctionServer connection unsuccessful.")
    
    def set_startstamp(self):
        """
        Synchronize logging using startstamp reference from rpi
        """
        startstampmsg = self.stub.set_startstamp(pb2.null)
        self.startstamp = startstampmsg.time

    def get_subject_info(self):
        """
        Sends null message to LoggingServer to get subject details
        """
        subject_info = self.stub.get_subject_info(pb2.null())
        return subject_info.startstamp, subject_info.subjectID, subject_info.trial_type, subject_info.trial_cond, subject_info.description, subject_info.usebackup

    def chop(self):
        """
        Kill LoggingServer from client(GUI)
        """
        response = self.stub.chop(pb2.beaver())
        return response

# Exoboot Controller Commands
    def set_quit(self, mybool=False):
        """
        Set quit thread event
        """
        receipt = self.stub.set_quit(pb2.quit(mybool=mybool))
        return receipt

    def set_pause(self, mybool=False):
        """
        Set pause thread event
        """
        receipt = self.stub.set_pause(pb2.pause(mybool=mybool))
        return receipt
    
    def set_log(self, mybool=False):
        """
        Set log thread event
        """
        receipt = self.stub.set_log(pb2.log(mybool=mybool))
        return receipt

    def set_torques(self, peak_torque_left=0, peak_torque_right=0):
        """
        Set exoboot torques
        """
        torque_msg = pb2.torques(peak_torque_left=peak_torque_left, peak_torque_right=peak_torque_right)
        receipt = self.stub.set_torque(torque_msg)
        return receipt
    
    def getpack(self, thread, field):
        """
        Get data from threads given fields
        """
        req_log = pb2.req_log(thread=thread, field=field)
        ret_val = self.stub.getpack(req_log)
        return ret_val.val

# Vickrey Specific
    def call(self, t, subject_bid, user_win_flag, current_payout, total_winnings):
        """
        Send results of Vickrey Auction
        """
        datadict = {"t": t, "subject_bid": subject_bid, "user_win_flag": user_win_flag,
                        "current_payout": current_payout, "total_winnings": total_winnings}
        msg = gen_msg_encode(datadict)
        response = self.stub.call(msg)
        return response
    
    def question(self, t, enjoyment, rpe):
        """
        Send post-auction survey results
        """
        datadict = {"t": t, "enjoyment": enjoyment, "rpe": rpe}
        msg = gen_msg_encode(datadict)
        response = self.stub.question(msg)
        return response

# VAS Specific
    def update_vas_info(self, btn_num, trial, pres):
        """
        Update overtime logging
        """
        datadict = {"btn_num": btn_num, "trial": trial, "pres": pres}
        msg = gen_msg_encode(datadict)
        receipt = self.stub.update_vas_info(msg)
        return receipt

    def slider_update(self, pitime, overtime_dict):
        """
        Send updated slider info
        """
        torques = []
        mvs = []
        for torque, mv in overtime_dict.items():
            torques.append(torque)
            mvs.append(mv)

        datadict = {"pitime": pitime, "torques": torques, "mvs": mvs}
        msg = gen_msg_encode(datadict)
        receipt = self.stub.slider_update(msg)
        return receipt

    def presentation_result(self, btn_option, trial, pres, torques, values):
        """
        Send updated slider info
        """
        datadict = {"btn_option": btn_option, "trial": trial, "pres": pres, "torques": torques, "values": values}
        msg = gen_msg_encode(datadict)
        receipt = self.stub.presentation_result(msg)
        return receipt

# JND Specific    
    def comparison_result(self, pres, prop, T_ref, T_comp, truth, answer):
        """
        Send comparison result message JND
        """
        datadict = {"pres": pres, "prop": prop, "T_ref": T_ref, "T_comp": T_comp, "truth": truth, "answer": answer}
        msg = gen_msg_encode(datadict)
        response = self.stub.comparison_result(msg)
        return response
    
    def comparison_result_stair(self, pres, prop, T_ref, T_comp, truth, answer):
        """
        Send comparison result message JND STAIR
        """
        datadict = {"pres": pres, "prop": prop, "T_ref": T_ref, "T_comp": T_comp, "truth": truth, "answer": answer}
        msg = gen_msg_encode(datadict)
        response = self.stub.comparison_result_stair(msg)
        return response

# PREF Specific
    def pref_result(self, pres, torque):
        """
        Send preference result message
        """
        datadict = {"pres": pres, "torque": torque}
        msg = gen_msg_encode(datadict)
        response = self.stub.pref_result(msg)
        return response

# General Message Test
    def gen_msg_test(self, datadict):
        """
        Testing purposes only
        """
        msg = self.gen_msg_encode(datadict)
        response = self.stub.gen_msg_test(msg)
        return response


class ExobootCommServicer(pb2_grpc.exoboot_over_networkServicer):
    """
    Communication between anything and pi

    This class is rpi side
    """
    def __init__(self, mainwrapper, startstamp, filingcabinet, usebackup, quit_event):
        super().__init__()
        self.mainwrapper = mainwrapper
        self.startstamp = startstamp
        self.filingcabinet = filingcabinet
        self.usebackup = usebackup
        self.quit_event = quit_event
    
        # file prefix from mainwrapper
        self.file_prefix = self.mainwrapper.file_prefix

        # Load backup or...
        loadstatus = False
        if self.usebackup:
            loadstatus = self.filingcabinet.loadbackup(self.file_prefix, rule="newest")

        # ... create new files
        if not loadstatus:
            match self.mainwrapper.trial_type.upper():
                case 'VICKREY':
                    auctionname = "{}_{}".format(self.file_prefix, "auction")
                    auctionpath = self.filingcabinet.newfile(auctionname, "csv", dictkey="auction")
                    
                    surveyname = "{}_{}".format(self.file_prefix, "survey")
                    surveypath = self.filingcabinet.newfile(surveyname, "csv", dictkey="survey")

                    with open(auctionpath, 'a', newline='') as f:
                        csv.writer(f).writerow(['t', 'subject_bid', 'user_win_flag', 'current_payout', 'total_winnings'])
                    with open(surveypath, 'a', newline='') as f:
                        csv.writer(f).writerow(['t', 'enjoyment', 'rpe'])

                case 'VAS':
                    overtimepath = ""
                    vasresultsname = "{}_{}".format(self.file_prefix, "vasresults")
                    vasresultspath = self.filingcabinet.newfile(vasresultsname, "csv", dictkey="vasresults")

                    with open(vasresultspath, 'a', newline='') as f:
                        header = ['btn_option', 'trial', 'pres']
                        for i in range(20): # TODO remove constant 20
                            header.append('torque{}'.format(i))
                            header.append('mv{}'.format(i))
                        csv.writer(f).writerow(header)

                case 'JND':
                    comparisonname = "{}_{}".format(self.file_prefix, "comparison")
                    comparisonpath = self.filingcabinet.newfile(comparisonname, "csv", dictkey="comparison")

                    # TODO: Add extra logging on pi here for kaernbach (check file_prefix for trial cond)
                    with open(comparisonpath, 'a', newline='') as f:
                        csv.writer(f).writerow(['pres', 'prop', 'T_ref', 'T_comp', 'truth', 'higher'])
                
                case 'PREF':
                    prefname = "{}_{}".format(self.file_prefix, "pref")
                    prefpath = self.filingcabinet.newfile(prefname, "csv", dictkey="pref")

                    with open(prefpath, 'a', newline='') as f:
                        csv.writer(f).writerow(['pres', 'torque'])

                case 'THERMAL':
                    pass

# General Methods
    def testconnection(self, request, context):
        print("Testing Connection: {}".format(request.msg))
        self.subject_name = request.msg
        return pb2.receipt(received=True)
    
    def get_subject_info(self, nullmsg, context):
        return pb2.subject_info(startstamp=self.mainwrapper.startstamp, 
                                subjectID=self.mainwrapper.subjectID,
                                trial_type=self.mainwrapper.trial_type,
                                trial_cond=self.mainwrapper.trial_cond,
                                description=self.mainwrapper.description,
                                usebackup=self.mainwrapper.usebackup)

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

    def set_log(self, logmsg, context):
        """
        Exoboot_Thread Command
        Set log event
        """
        log = logmsg.mybool
        print("LOG COMMAND: {}".format(log))
        if log:
            self.mainwrapper.log_event.clear()
        else:
            self.mainwrapper.log_event.set()
        return pb2.receipt(received=True)

    def set_torque(self, torquemsg, context):
        """
        Exoboot_Thread Command
        Sets peak torque of exoboots
        """
        peak_torque_left  = torquemsg.peak_torque_left
        peak_torque_right = torquemsg.peak_torque_right

        # Set torques in GSE
        self.mainwrapper.gse_thread.set_peak_torque_left(peak_torque_left)
        self.mainwrapper.gse_thread.set_peak_torque_right(peak_torque_right)

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
        """
        Log auction results
        """
        datadict = gen_msg_decode(resultmsg)
        t = datadict["t"]
        subject_bid = datadict["subject_bid"]
        user_win_flag = datadict["user_win_flag"]
        current_payout = datadict["current_payout"]
        total_winnings = datadict["total_winnings"]

        print("Received auction results: {}, {}, {}, {}, {}".format(t, subject_bid, user_win_flag, current_payout, total_winnings))
        datalist = [t, subject_bid, user_win_flag, current_payout, total_winnings]

        auctionpath = self.filingcabinet.getpath("auction")
        with open(auctionpath, 'a', newline='') as f: 
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)
    
    def question(self, surveymsg, context):
        """
        Log server results
        """
        datadict = gen_msg_decode(surveymsg)
        t = datadict["t"]
        enjoyment = datadict["enjoyment"]
        rpe = datadict["rpe"]

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
        datadict = gen_msg_decode(vasinfomsg)
        btn_num = int(datadict["btn_num"])
        trial = int(datadict["trial"])
        pres = int(datadict["pres"])

        print("\nSTARTING PRESENTATION: {} {} {}\n{}\n".format(btn_num, trial, pres, str(datetime.datetime.now())))
        overtimename = "B{}_T{}_P{}_vas_overtime".format(self.file_prefix, trial, pres)
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
        datadict = gen_msg_decode(slidermsg)
        pitime = datadict["pitime"]
        torques = datadict["torques"]
        mvs = datadict["mvs"]

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
        datadict = gen_msg_decode(presmsg)
        btn_option = int(datadict["btn_option"])
        trial = int(datadict["trial"])
        pres = int(datadict["pres"])
        torques = datadict["torques"]
        values = datadict["values"]

        print("\nFINISHED PRESENTATION: {} {} {}\n{}\n".format(btn_option, trial, pres, str(datetime.datetime.now())))
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
        """
        Log comparison result for JND
        """
        datadict = gen_msg_decode(compmsg)
        pres = datadict["pres"]
        prop = datadict["prop"]
        T_ref = datadict["T_ref"]
        T_comp = datadict["T_comp"]
        truth = datadict["truth"]
        answer = datadict["answer"]

        print("Received comparison results: {}, {}, {}, {}, {}, {}".format(pres, prop, T_ref, T_comp, truth, answer))
        datalist = [pres, prop, T_ref, T_comp, truth, answer]

        comparisonpath = self.filingcabinet.getpath("comparison")
        with open(comparisonpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)
    
    def comparison_result_stair(self, compmsg, context):
        """
        Log comparison result for JND STAIR
        """
        datadict = gen_msg_decode(compmsg)
        pres = datadict["pres"]
        prop = datadict["prop"]
        T_ref = datadict["T_ref"]
        T_comp = datadict["T_comp"]
        truth = datadict["truth"]
        answer = datadict["answer"]

        print("Received comparison results: {}, {}, {}, {}, {}, {}".format(pres, prop, T_ref, T_comp, truth, answer))
        datalist = [pres, prop, T_ref, T_comp, truth, answer]   # TODO: change data list to include stair info

        comparisonpath = self.filingcabinet.getpath("comparison")
        with open(comparisonpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)
    
# Pref Specific
    def pref_result(self, prefmsg, context):
        datadict = gen_msg_decode(prefmsg)
        pres = datadict["pres"]
        torque = datadict["torque"]

        print("Received preference results: {}, {}".format(pres, torque))
        datalist = [pres, torque]

        prefpath = self.filingcabinet.getpath("pref")
        with open(prefpath, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)

# General Message Test
    def gen_msg_test(self, gen_msg, context):
        """
        Testing purposes only
        """
        return pb2.receipt(received=True)

class ExobootRemoteServerThread(BaseThread):
    """
    Thread class for receiving remote commands

    Runs until quit_event is cleared

    Does not pause
    """
    def __init__(self, mainwrapper, startstamp, filingcabinet, usebackup=False, name='exoboot_remote_thread', daemon=True, quit_event=Type[threading.Event], pause_event=Type[threading.Event], log_event=Type[threading.Event]):
        super().__init__(name=name, daemon=daemon, pause_event=pause_event, quit_event=quit_event)
        self.mainwrapper = mainwrapper
        self.exoboot_remote_servicer = ExobootCommServicer(self.mainwrapper, startstamp, filingcabinet, usebackup=usebackup, quit_event=self.quit_event)
        self.target_IP = ''
    
    def set_target_IP(self, target_IP):
        self.target_IP = target_IP 

    def start_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_exoboot_over_networkServicer_to_server(self.exoboot_remote_servicer, server)
        server.add_insecure_port(self.target_IP)
        server.start()
        server.wait_for_termination()

    def run(self):
        while self.quit_event.is_set():
            self.start_server()


def gen_msg_encode(datadict):
    """
    Encode a gen_msg with datadicts contents
    Only accepts string, float, and bool vecs
    """
    mygenmsg = pb2.gen_msg()
    for field, value in datadict.items():
        if value or isinstance(value, bool) or isinstance(value, int):
            if isinstance(value, list):
                exampleval = value[0]
                if isinstance(exampleval, str):
                    mygenmsg.stringvecs.add(field=field, value=value)
                elif isinstance(exampleval, bool):
                    mygenmsg.boolvecs.add(field=field, value=value)
                elif isinstance(exampleval, float) or isinstance(exampleval, int):
                    mygenmsg.floatvecs.add(field=field, value=value)
            elif isinstance(value, str):
                mygenmsg.stringsingles.add(field=field, value=value)
            elif isinstance(value, bool):
                mygenmsg.boolsingles.add(field=field, value=value)
            elif isinstance(value, float) or isinstance(value, int):
                mygenmsg.floatsingles.add(field=field, value=value)
            else:
                pass
    return mygenmsg

def gen_msg_decode(genmsg):
    """
    Recreate dict from gen_msg
    """
    datadict = {}
    for instances in [genmsg.stringsingles, genmsg.stringvecs, genmsg.floatsingles, genmsg.floatvecs, genmsg.boolsingles, genmsg.boolvecs]:
        if instances:
            for instance in instances:
                datadict[instance.field] = instance.value
    return datadict


if __name__ == "__main__":
    """
    IMPORTANT REMINDER
    
    Make sure to convert types back into basic python types

    Example: numpy.int32 will not register in gen_msg_encode

    Need to convert back into python int

    TODO read this reminder
    """
    very_important_data = {"pres": 2, "prop": 2, "T_ref": 29, "T_comp": 40, "truth": 1, "answer": 0}
    print("ORIGINAL: {}".format(very_important_data))

    # Encode dict into gen_msg
    msg = gen_msg_encode(very_important_data)
    print("MSG: {}".format(msg))

    # Decode gen_msg back into dict
    recreated_dict = gen_msg_decode(msg)
    print("\nRECREATION: {}".format(recreated_dict))

    print("\nCheck Recreation...")
    print("Should include only string, float, and bool singles and vecs")
    for field in very_important_data.keys():
        try:
            assert recreated_dict[field] == very_important_data[field]
        except:
            print("\tMissing: {}".format(field))
