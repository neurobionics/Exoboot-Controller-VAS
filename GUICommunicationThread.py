import threading
import grpc 
# import Message_pb2
# import Message_pb2_grpc
import gui2controller2_pb2
import gui2controller2_pb2_grpc
from concurrent import futures
from typing import Type
import time

import config
from utils import MovingAverageFilter

class GUI_thread(threading.Thread):
    def __init__(self, quit_event=Type[threading.Event], name='GUICommunication'):

        super().__init__(name = name)
        self.quit_event = quit_event
    
    class CommunicationService(gui2controller2_pb2_grpc.CommunicationServiceServicer):
        def __init__(self, GUI_thread):
            self.GUI_thread = GUI_thread
            
        def GUI_Messenger(self, request, context):
            # Printing out the request from the client        
            requested_torque = request.logging_data[0]              # Current Torque Experienced(Nm)
            requested_slider_btn = request.logging_data[1]          # Adjusted Slider Btn
            requested_slider_value = request.logging_data[2]        # Adjusted Slider Value($)
            requested_confirm_btn_pressed = request.logging_data[3] # Confirm Button Pressed
            
            print("New commanded torque is:", config.GUI_commanded_torque)
            
            if requested_torque == 'nan':
                config.adjusted_slider_btn = str(requested_slider_btn)
                config.adjusted_slider_value = float(requested_slider_value)
                config.confirm_btn_pressed = requested_confirm_btn_pressed
            else: 
                config.GUI_commanded_torque = float(requested_torque)
                print("New commanded torque is:", config.GUI_commanded_torque)
                
                config.adjusted_slider_btn = str(requested_slider_btn)
                config.adjusted_slider_value = float(requested_slider_value)
                config.confirm_btn_pressed = requested_confirm_btn_pressed
            
            # Sending a Null response to GUI
            return gui2controller2_pb2.Null()
    
    def starting_server(self):
        print("Starting Server -- For receiving Peak Torques, $-Values, etc...")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gui2controller2_pb2_grpc.add_CommunicationServiceServicer_to_server(self.CommunicationService(self),server)
        server.add_insecure_port(config.server_ip)
        server.start()
        server.wait_for_termination()        

    def run(self):
        # Period Tracker
        period_tracker = MovingAverageFilter(size=300)
        prev_end_time = time.time()

        while self.quit_event.is_set():
            self.starting_server()

            # Update Period Tracker and config
            end_time = time.time()
            period_tracker.update(end_time - prev_end_time)
            prev_end_time = end_time
            config.gui_communication_thread_frequency = 1/period_tracker.average()