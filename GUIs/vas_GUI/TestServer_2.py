"""Communication Server-side test script"""
import grpc
import gui2controller2_pb2
import gui2controller2_pb2_grpc
from concurrent import futures
import config
import os
import csv

class CommunicationService(gui2controller2_pb2_grpc.CommunicationServiceServicer):
    
    def GUI_Messenger(self, request, context):
        # Printing out the request from the client
        # print("Server received data:", request.logging_data)
        
        requested_torque = request.logging_data[0]              # Current Torque Experienced(Nm)
        requested_slider_btn = request.logging_data[1]          # Adjusted Slider Btn
        requested_slider_value = request.logging_data[2]        # Adjusted Slider Value($)
        requested_confirm_btn_pressed = request.logging_data[3] # Confirm Button Pressed
        
        if requested_torque == 'nan':
            adjusted_slider_btn = str(requested_slider_btn)
            adjusted_slider_value = float(requested_slider_value)
            confirm_btn_pressed = requested_confirm_btn_pressed
        else: 
            config.gui_commanded_torque = float(requested_torque)
            adjusted_slider_btn = str(requested_slider_btn)
            adjusted_slider_value = float(requested_slider_value)
            confirm_btn_pressed = requested_confirm_btn_pressed
            
        # log the values to a csv file
        filename = 'Vickrey_VAS_GUI\vas_GUI\test_log.csv'
        data_array = [config.gui_commanded_torque, 
                    adjusted_slider_btn, 
                    adjusted_slider_value, 
                    confirm_btn_pressed]
        
        print("data array:", data_array)
        self.logging(filename, data_array)
        
        # Sending the Null response(to close the communication loop)
        return gui2controller2_pb2.Null()
        
    def logging(self, filename, datapoint_array):
        with open(filename, 'a') as f:
            writer = csv.writer(f, lineterminator='\n',quotechar='|')
            writer.writerow(datapoint_array)
    
def starting_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gui2controller2_pb2_grpc.add_CommunicationServiceServicer_to_server(CommunicationService(),server)
    server.add_insecure_port(config.server_ip)#config.client_ip)  
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    starting_server()
