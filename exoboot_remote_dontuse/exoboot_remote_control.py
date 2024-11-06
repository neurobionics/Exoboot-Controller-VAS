import csv, grpc, threading

from typing import Type
from concurrent import futures

import exoboot_remote.exoboot_remote_pb2 as pb2
import exoboot_remote.exoboot_remote_pb2_grpc as pb2_grpc

from BaseExoThread import BaseThread

class ExobootRemoteClient:
    """
    Client running on network
    """
    def __init__(self, server_IP):
        self.channel = grpc.insecure_channel(server_IP)
        self.stub = pb2_grpc.exoboot_over_networkStub(self.channel)
        self.startstamp = 0

# General Methods    
    def testconnection(self, guiname=None):
        """
        Sends test message to LoggingServer
        """
        msg = pb2.testmsg(msg="Hello from {}".format(guiname))
        response = self.stub.testconnection(msg)
        
        # See response received
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
    def set_pause(self, mybool):
        pause_msg = pb2.pause(mybool=mybool)
        receipt = self.stub.set_pause(pause_msg)
        return receipt
    
    def set_quit(self, mybool):
        quit_msg = pb2.quit(mybool=mybool)
        receipt = self.stub.set_quit(quit_msg)
        return receipt
    
    def set_log(self, mybool):
        log_msg = pb2.log(mybool=mybool)
        receipt = self.stub.set_log(log_msg)
        return receipt

    def set_torques(self, peak_torque_left=0, peak_torque_right=0):
        torque_msg = pb2.torques(peak_torque_left=peak_torque_left, peak_torque_right=peak_torque_right)
        receipt = self.stub.set_torque(torque_msg)
        return receipt

# Vickrey Specific
    def call(self, t, subject_bid, user_win_flag, current_payout, total_winnings):
        """
        Send results of Vickrey Auction
        """
        resultmsg = pb2.result(t=t, subject_bid=subject_bid, user_win_flag=user_win_flag,
                         current_payout=current_payout, total_winnings=total_winnings)
        response = self.stub.call(resultmsg)
        return response
    
    def question(self, t, enjoyment, rpe):
        """
        Send post-auction survey results
        """
        surveymsg = pb2.survey(t=t, enjoyment=enjoyment, rpe=rpe)
        response = self.stub.question(surveymsg)
        return response
    
    def newwalk(self, t):
        """
        Send new walk info
        """
        walkmsg = pb2.walkmsg(t=t)
        response = self.stub.newwalk(walkmsg)
        return response

# VAS Specific
    def update_vas_info(self, btn_num, trial, pres):
        """
        Update overtime logging
        """
        msg = pb2.vas_info(btn_num=btn_num, trial=trial, pres=pres)
        response = self.stub.update_vas_info(msg)
        return response

    def slider_update(self, pitime, overtime_dict):
        """
        Send updated slider info
        """
        torques = []
        mvs = []
        for torque, mv in overtime_dict.items():
            torques.append(torque)
            mvs.append(mv)

        msg = pb2.slider(pitime=pitime, torques=torques, mvs=mvs)
        response = self.stub.slider_update(msg)
        return response

    def presentation_result(self, btn_option, trial, pres, torques, values):
        """
        Send updated slider info
        """
        msg = pb2.presentation(btn_option=btn_option, trial=trial, pres=pres, torques=torques, values=values)
        response = self.stub.presentation_result(msg)
        return response
    
    def newpres(self, btn_num, trial, pres):
        """
        Send thread new btp info
        """
        msg = pb2.vas_info(btn_num=btn_num, trial=trial, pres=pres)
        response = self.stub.newpres(msg)
        return response

# JND Specific    
    def comparison_result(self, walk, pres, prop, T_ref, T_comp, truth, answer):
        compmsg = pb2.comparison(walk=walk, pres=pres, prop=prop, T_ref=T_ref, T_comp=T_comp, truth=truth, answer=answer)
        response = self.stub.comparison_result(compmsg)
        return response
    
    def newwalkjnd(self, walk):
        msg = pb2.walkmsgjnd(walk=walk)
        response = self.stub.newwalk(msg)
        return response

# PREF Specific
    def pref_result(self, pres, torque):
        prefmsg = pb2.preference(pres=pres, torque=torque)
        response = self.stub.pref_result(prefmsg)
        return response


class ExobootCommServicer(pb2_grpc.exoboot_over_networkServicer):
    """
    Communication between anything and pi

    This class is rpi side
    """
    def __init__(self, mainwrapper, startstamp, filingcabinet, usebackup, quit_event, log_event):
        super().__init__()
        self.mainwrapper = mainwrapper
        self.loggingnexus = self.mainwrapper.loggingnexus
        self.filingcabinet = filingcabinet

        self.startstamp = startstamp
        self.usebackup = usebackup
        self.quit_event = quit_event
        self.log_event = log_event
    
        # file prefix from mainwrapper
        self.file_prefix = self.mainwrapper.file_prefix

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
        self.quit_event.clear()
        return pb2.receipt(received=True)

# Exoboot Controller Commands
    def set_pause(self, pause_msg, context):
        """
        Exoboot_Thread Command
        Pauses threads in main
        """
        pause = pause_msg.mybool
        if pause:
            self.mainwrapper.pause_event.clear()
        else:
            self.mainwrapper.pause_event.set()
        return pb2.receipt(received=True)
    
    def set_log(self, log_msg, context):
        """
        Set log event remotely
        """
        log = log_msg.mybool
        if log:
            self.mainwrapper.log_event.clear()
        else:
            self.mainwrapper.log_event.set()
        return pb2.receipt(received=True)

    def set_quit(self, quit_msg, context):
        """
        Exoboot_Thread Command
        Quits execution in main
        """
        quit = quit_msg.mybool
        if quit:
            self.mainwrapper.quit_event.clear()
        else:
            self.mainwrapper.quit_event.set()
        return pb2.receipt(received=True)

    def set_torque(self, torque_msg, context):
        """
        Exoboot_Thread Command
        Sets peak torque of exoboots
        """
        # Printing out the request from the client
        peak_torque_left  = torque_msg.peak_torque_left
        peak_torque_right = torque_msg.peak_torque_right

        # Set torques in GSE
        self.mainwrapper.gse_thread.set_peak_torque_left(peak_torque_left)
        self.mainwrapper.gse_thread.set_peak_torque_right(peak_torque_right)

        return pb2.receipt(received=True)

# Vickrey Auction Specific
    def call(self, resultmsg, context):
        """
        Log auction result
        """
        t = resultmsg.t
        subject_bid = resultmsg.subject_bid
        user_win_flag = resultmsg.user_win_flag
        current_payout = resultmsg.current_payout
        total_winnings = resultmsg.total_winnings

        print("Received auction results: {}, {}, {}, {}, {}".format(t, subject_bid, user_win_flag, current_payout, total_winnings))
        self.filingcabinet.writerow("auction", [t, subject_bid, user_win_flag, current_payout, total_winnings])

        return pb2.receipt(received=True)
    
    def question(self, surveymsg, context):
        """
        Log survey result
        """
        t = surveymsg.t
        enjoyment = surveymsg.enjoyment
        rpe = surveymsg.rpe
        self.filingcabinet.writerow("survey", [t, enjoyment, rpe])

        return pb2.receipt(received=True)

    def newwalk(self, walkmsg, context):
        """
        Update pi threads logging file
        """
        t = 2 * walkmsg.t
        for thread in self.loggingnexus.thread_names:
            self.loggingnexus.update_suffix("t{}".format(t), thread)

        return pb2.receipt(received=True)

# VAS Specific
    def update_vas_info(self, vasinfomsg, context):
        """
        Start overtime logging in a new file
        """
        btn = int(vasinfomsg.btn_num)
        trial = int(vasinfomsg.trial)
        pres = int(vasinfomsg.pres)

        print("Received updated vas info: ", btn, trial, pres)
        header = ['pitime']
        for i in range(btn):
            header.append("Torque{}".format(i))
            header.append("MV{}".format(i))

        overtimename = "{}_overtime_B{}_T{}_P{}".format(self.file_prefix, btn, trial, pres)
        self.filingcabinet.newfile(overtimename, "csv", dictkey="overtime", header=header)

        return pb2.receipt(received=True)

    def slider_update(self, slidermsg, context):
        """
        Send updated slider info
        """
        pitime = slidermsg.pitime
        torques = slidermsg.torques
        mvs = slidermsg.mvs

        data = [pitime]
        for torque, mv in zip(torques, mvs):
            data.append(torque)
            data.append(mv)
        self.filingcabinet.writerow("overtime", data)

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

        data = [btn_option, trial, pres]
        for t, mv in zip(torques, values):
            data.append(t)
            data.append(mv)
        self.filingcabinet.writerow("vasresults", data)

        return pb2.receipt(received=True)

    def newpres(self, vasinfomsg, context):
        """
        Update thread logging csv
        """
        btn = int(vasinfomsg.btn_num)
        trial = int(vasinfomsg.trial)
        pres = int(vasinfomsg.pres)
        suffix = "B{}_T{}_P{}".format(btn, trial, pres)

        for thread in self.loggingnexus.thread_names:
            self.loggingnexus.update_suffix(suffix, thread)

        return pb2.receipt(received=True)

# JND Specific
    def comparison_result(self, compmsg, context):
        """
        Log comparison result
        """
        walk = compmsg.walk
        pres = compmsg.pres
        prop = compmsg.prop
        T_ref = compmsg.T_ref
        T_comp = compmsg.T_comp
        truth = compmsg.truth
        answer = compmsg.answer
        self.filingcabinet.writerow("comparison", [walk, pres, prop, T_ref, T_comp, truth, answer])

        return pb2.receipt(received=True)
    
    def newwalkjnd(self, walkmsgjnd, context):
        """
        Update threads logging csv files
        """
        walk = int(walkmsgjnd.walk)
        for thread in self.loggingnexus.thread_names:
            self.loggingnexus.update_suffix("walk{}".format(walk), thread)

        return pb2.receipt(received=True)
    
# Pref Specific
    def pref_result(self, prefmsg, context):
        """
        Log pref results
        """
        pres = prefmsg.pres
        torque = prefmsg.torque
        self.filingcabinet.writerow("pref", [pres, torque])

        return pb2.receipt(received=True)


class ExobootRemoteServerThread(BaseThread):
    """
    Thread class for receiving remote commands

    Runs until quit_event is cleared

    Does not pause
    """
    def __init__(self, mainwrapper, startstamp, filingcabinet, usebackup=False, name='exoboot_remote_thread', daemon=True, backupexceptions=None, pause_event=Type[threading.Event], quit_event=Type[threading.Event], log_event=Type[threading.Event]):
        super().__init__(name, daemon, pause_event, quit_event, log_event)
        self.mainwrapper = mainwrapper
        self.exoboot_remote_servicer = ExobootCommServicer(self.mainwrapper, startstamp, filingcabinet, usebackup=usebackup, quit_event=self.quit_event, log_event=self.log_event)
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
