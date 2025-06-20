import csv
import grpc
import threading
from typing import Type
from concurrent import futures

import exoboot_remote_pb2 as pb2
import exoboot_remote_pb2_grpc as pb2_grpc
from src.exo.BaseExoThread import BaseThread


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
        receipt = self.stub.set_quit(pb2.quit(mybool=mybool))
        return receipt

    def set_pause(self, mybool=False):
        receipt = self.stub.set_pause(pb2.pause(mybool=mybool))
        return receipt

    def set_log(self, mybool=False):
        receipt = self.stub.set_log(pb2.log(mybool=mybool))
        return receipt

    def set_torques(self, peak_torque_left=0, peak_torque_right=0):
        torque_msg = pb2.torques(peak_torque_left=peak_torque_left, peak_torque_right=peak_torque_right)
        receipt = self.stub.set_torque(torque_msg)
        return receipt

    def getpack(self, thread, field):
        req_log = pb2.req_log(thread=thread, field=field)
        ret_val = self.stub.getpack(req_log)
        return ret_val.val

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
    def update_vas_info(self, btn_num, trial, pres):
        """
        Update overtime logging
        """
        msg = pb2.vas_info(btn_num=btn_num, trial=trial, pres=pres)
        _ = self.stub.update_vas_info(msg)
        return None

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

    # JND Specific
    def comparison_result(self, pres, prop, T_ref, T_comp, truth, answer):
        compmsg = pb2.comparison(pres=pres, prop=prop, T_ref=T_ref, T_comp=T_comp, truth=truth, answer=answer)
        response = self.stub.comparison_result(compmsg)
        return response

    def comparison_result_stair(self, pres, prop, T_ref, T_comp, truth, answer):
        # TODO: modify grpc msg to server to include stair info
        compmsg = pb2.comparison_stair(pres=pres, prop=prop, T_ref=T_ref, T_comp=T_comp, truth=truth, answer=answer)
        response = self.stub.comparison_result_stair(compmsg)
        return response

    # PREF Specific
    def pref_result(self, pres, torque):
        prefmsg = pb2.preference(pres=pres, torque=torque)
        response = self.stub.pref_result(prefmsg)
        return response