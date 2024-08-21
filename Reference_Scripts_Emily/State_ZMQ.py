# import the necessary packages
import zmq
import numpy as np

class ZmqVICONpi:
    def __init__(self, connectport="tcp://192.168.1.149:5555"):
        self.context = zmq.Context()
        self.socketB = self.context.socket(zmq.SUB)
        self.socketB.connect(connectport)
        self.socketB.setsockopt_string(zmq.SUBSCRIBE, "")

        self.data_out = -2

    def update(self):
        """ read all messages, then send data. """
        while True:
            try:      
                message = self.socketB.recv(zmq.NOBLOCK)
                self.data_out=int(message)
            except zmq.error.Again:
                break
            
        return self.data_out

    def stop(self):
        zmq.ContextTerminated