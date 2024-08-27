import threading
import grpc
from concurrent import futures
import exoboot_remote_pb2 as pb2_r
import exoboot_remote_pb2_grpc as pb2_grpc_r

from typing import Type
import time

from utils import MovingAverageFilter
from constants import PI_IP

from BaseExoThread import BaseThread

class ExobootCommServicer(pb2_grpc_r.exoboot_over_networkServicer):
    """
    Communication between anything and pi

    This class is rpi side
    """
    def __init__(self, mainwrapper):
        super().__init__()
        self.mainwrapper = mainwrapper

    def send_subject_info(self, infomsg, context):
        """
        Set subject info in Exoboot_Wrapper
        """
        self.mainwrapper.set_subject_info(infomsg.subjectID, infomsg.trial_type, infomsg.description)
        return pb2_r.receipt_exoboot(received=True)

    def set_pause(self, pause_msg, context):
        pause = pause_msg.mybool

        if pause:
            self.mainwrapper.pause_event.clear()
        else:
            self.mainwrapper.pause_event.set()

        return pb2_r.receipt_exoboot(received=True)

    def set_quit(self, quit_msg, context):
        quit = quit_msg.mybool

        if quit:
            self.mainwrapper.quit_event.clear()
        else:
            self.mainwrapper.quit_event.set()

        return pb2_r.receipt_exoboot(received=True)

    def set_torque(self, torque_msg, context):
        # Printing out the request from the client        
        peak_torque_left  = torque_msg.peak_torque_left
        peak_torque_right = torque_msg.peak_torque_right

        # Set torques in GSE
        self.mainwrapper.gse_thread.set_peak_torque_left(peak_torque_left)
        self.mainwrapper.gse_thread.set_peak_torque_right(peak_torque_right)

        return pb2_r.receipt_exoboot(received=True)


class ExobootRemoteServerThread(BaseThread):
    """
    Thread class for receiving remote commands

    Runs until quit_event is cleared
     
    Does not pause
    """
    def __init__(self, mainwrapper, name='exoboot_remote_thread', daemon=True, pause_event=Type[threading.Event], quit_event=Type[threading.Event]):
        super().__init__(name=name, daemon=daemon, pause_event=pause_event, quit_event=quit_event)
        self.mainwrapper = mainwrapper
        self.exoboot_remote_servicer = ExobootCommServicer(self.mainwrapper)
        self.fields = []
    
    def starting_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc_r.add_exoboot_over_networkServicer_to_server(self.exoboot_remote_servicer, server)
        server.add_insecure_port(PI_IP)
        server.start()
        server.wait_for_termination()        

    def run(self):
        while self.quit_event.is_set():
            self.starting_server()


class ExobootRemoteClient:
    """
    Client running on network
    """
    def __init__(self):
        self.channel = grpc.insecure_channel(PI_IP)
        self.stub = pb2_grpc_r.exoboot_over_networkStub(self.channel)

    def send_subject_info(self, subjectID, trial_type, description):
        infomsg = pb2_r.subject_info_eb(subjectID=subjectID, trial_type=trial_type, description=description)
        receipt = self.stub.send_subject_info(infomsg)
        return receipt

    def set_pause(self, mybool=False):
        pause_msg = pb2_r.pause(mybool=mybool)
        receipt = self.stub.set_pause(pause_msg)
        return receipt
    
    def set_quit(self, mybool=False):
        quit_msg = pb2_r.quit(mybool=mybool)
        receipt = self.stub.set_quit(quit_msg)
        return receipt

    def set_torques(self, peak_torque_left=0, peak_torque_right=0):
        torque_msg = pb2_r.torques(peak_torque_left=peak_torque_left, peak_torque_right=peak_torque_right)
        receipt = self.stub.set_torque(torque_msg)
        return receipt
