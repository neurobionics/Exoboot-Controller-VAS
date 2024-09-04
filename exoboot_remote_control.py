import csv, time, grpc, threading
from concurrent import futures
import exoboot_remote_pb2 as pb2
import exoboot_remote_pb2_grpc as pb2_grpc

from typing import Type

from utils import MovingAverageFilter
from constants import PI_IP

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
    def testconnection(self, guiname='none'):
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
        subject_info = self.stub.get_subject_info(pb2.testmsg(msg='TOREMOVE'))
        return subject_info.subjectID, subject_info.trial_type, subject_info.description

    def chop(self):
        """
        Kill LoggingServer from client(GUI)
        """
        response = self.stub.chop(pb2.beaver())
        return response

# Exoboot Controller Commands
    def set_pause(self, mybool=False):
        pause_msg = pb2.pause(mybool=mybool)
        receipt = self.stub.set_pause(pause_msg)
        return receipt
    
    def set_quit(self, mybool=False):
        quit_msg = pb2.quit(mybool=mybool)
        receipt = self.stub.set_quit(quit_msg)
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

# VAS Specific   
    def slider_update(self, torque, pos):
        """
        Send updated slider info
        """
        # TODO add pitime to slider message
        msg = pb2.slider(torque=torque, pos = pos)
        response = self.stub.slider_update(msg)
        return response

    def presentation_result(self, torque, pos):
        """
        Send updated slider info
        """
        msg = pb2.presentation(torque=torque, pos = pos)
        response = self.stub.presentation_result(msg)
        return response

# JND Specific    
    def comparison_result(self, torques, higher):
        msg = pb2.comparison(torques=torques, higher=higher)
        response = self.stub.comparison_result(msg)
        return response


class ExobootCommServicer(pb2_grpc.exoboot_over_networkServicer):
    """
    Communication between anything and pi

    This class is rpi side
    """
    def __init__(self, mainwrapper, startstamp, quit_event):
        super().__init__()
        self.mainwrapper = mainwrapper
        self.startstamp = startstamp
        self.quit_event = quit_event
    
        # file prefix from mainwrapper
        self.file_prefix = self.mainwrapper.file_prefix

# General Methods
    def testconnection(self, request, context):
        print("Testing Connection: {}".format(request.msg))
        self.subject_name = request.msg
        return pb2.receipt(received=True)
    
    def get_startstamp(self, nullmsg, context):
        return pb2.startstamp(time=self.startstamp)
    
    def get_subject_info(self, nullmsg, context):
        return pb2.subject_info(subjectID=self.subjectID, trial_type=self.trial_type, description=self.description)

    def chop(self, beaver, context):
        """
        Kill rpi from Client
        """
        self.quit_event.set()
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
        t = resultmsg.t
        subject_bid = resultmsg.subject_bid
        user_win_flag = resultmsg.user_win_flag
        current_payout = resultmsg.current_payout
        total_winnings = resultmsg.total_winnings

        print("Received auction results: {}, {}, {}, {}, {}".format(t, subject_bid, user_win_flag, current_payout, total_winnings))
        datalist = [t, subject_bid, user_win_flag, current_payout, total_winnings]

        auction_filename = self.file_prefix + '_auction.csv'
        with open(auction_filename, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)
    
    def question(self, surveymsg, context):
        t = surveymsg.t
        enjoyment = surveymsg.enjoyment
        rpe = surveymsg.rpe

        print("Received survey results: {}, {}, {}".format(t, enjoyment, rpe))
        datalist = [t, enjoyment, rpe]

        surveyfilename = self.file_prefix + '_survey.csv'
        with open(surveyfilename, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

        return pb2.receipt(received=True)

# VAS Specific
    def slider_update(self, slidermsg, context):
        """
        Send updated slider info
        """
        torque = slidermsg.torque
        pos = slidermsg.pos
        print("Torque: {} to {}".format(torque, pos))

        # TODO include overtime logging

        return pb2.receipt(received=True)
    
    def presentation_result(self, presmsg, context):
        """
        Send updated slider info
        """
        trial = presmsg.trial
        pres_num = presmsg.pres_num
        torques = presmsg.torques
        pos = presmsg.pos

        print("Received presentation results: {}, {}, {}, {}".format(trial, pres_num, torques, pos))
        datalist = [trial, pres_num, torques, pos]
        vasfilename = self.file_prefix + '_vas_results.csv'
        with open(vasfilename, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)
        return pb2.receipt(received=True)

# JND Specific  
    def comparison_result(self, compmsg):
        torques = compmsg.torques
        higher = compmsg.higher
        
        print("Received comparison results: {}, {}".format(torques, higher))
        return pb2.receipt(received=True)


class ExobootRemoteServerThread(BaseThread):
    """
    Thread class for receiving remote commands

    Runs until quit_event is cleared

    Does not pause
    """
    def __init__(self, mainwrapper, startstamp, name='exoboot_remote_thread', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        super().__init__(name=name, daemon=daemon, pause_event=pause_event, quit_event=quit_event)
        self.mainwrapper = mainwrapper
        self.exoboot_remote_servicer = ExobootCommServicer(self.mainwrapper, startstamp, quit_event=self.quit_event)
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
