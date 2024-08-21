import csv

import grpc
from concurrent import futures
import auction_pb2 as pb2
import auction_pb2_grpc as pb2_grpc

from constants import *

class AuctionHouse(pb2_grpc.auctionServicer):
    # Logs user bids and displays win/loss for experimenter
    def __init__(self):
        self.subject_name = input("Subject name: ")
        self.bid = 0

        self.auctionfilename = "{}_auction.csv".format(self.subject_name)
        self.surveyfilename = "{}_survey.csv".format(self.subject_name)

        self.auctionheader = ["t", "subject_bid", "user_win_flag", "current_payout", "total_winnings"]
        self.surveyheader = ["t", "enjoyment", "rpe"]

        with open(self.auctionfilename, 'a', newline='') as f:
            csv.writer(f).writerow(self.auctionheader)
        with open(self.surveyfilename, 'a', newline='') as f:
            csv.writer(f).writerow(self.surveyheader)

        print("\nStarting auctions\n")

    def testconnection(self, request, context):
        print("Testing Connection: {}".format(request.msg))
        self.subject_name = request.msg
        return pb2.receipt(received=True)

    def call(self, resultmsg, context):
        t = resultmsg.t
        subject_bid = resultmsg.subject_bid
        user_win_flag = resultmsg.user_win_flag
        current_payout = resultmsg.current_payout
        total_winnings = resultmsg.total_winnings

        self.logauction(t, subject_bid, user_win_flag, current_payout, total_winnings)

        return pb2.receipt(received=True)
    
    def question(self, surveymsg, context):
        t = surveymsg.t
        enjoyment = surveymsg.enjoyment
        rpe = surveymsg.rpe

        self.logsurvey(t, enjoyment, rpe)

        return pb2.receipt(received=True)
    
    def treadmill_message(self, treadmillmsg, context):
        state = treadmillmsg.state
        if state:
            print("\nBEGIN/START THE TREADMILL NOW\n")
        else:
            print("\nCEASE/STOP THE TREADMILL NOW\n")
        
        return pb2.receipt(received=True)
    
    def logauction(self, t, subject_bid, user_win_flag, current_payout, total_winnings):
        datalist = [t, subject_bid, user_win_flag, current_payout, total_winnings]
        print("Received auction results: {}, {}, {}, {}, {}".format(t, subject_bid, user_win_flag, current_payout, total_winnings))

        with open(self.auctionfilename, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)

    def logsurvey(self, t, enjoyment, rpe):
        datalist = [t, enjoyment, rpe]
        print("Received survey results: {}, {}, {}".format(t, enjoyment, rpe))

        with open(self.surveyfilename, 'a', newline='') as f:
            csv.writer(f).writerow(datalist)


def start_auction():
    auctionhouse = AuctionHouse()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_auctionServicer_to_server(auctionhouse, server)
    server.add_insecure_port(CLIENT_IP)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    try:
        print("Starting Auction House")
        start_auction()
    except KeyboardInterrupt:
        print("Exiting")