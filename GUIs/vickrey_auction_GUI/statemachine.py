from constants import *
from Robobidders import *

# Statemachine class
class VA_StateMachine:
    def __init__(self, screenmanager):
        self.sm = screenmanager

        # Init RoboBidders
        self.robomodel = roboModel(k_RB, b_RB, 2)
        self.auction_tally = 0 # Starts from 0th auction

        # Auction state
        self.state = False
        self.prev_state = False
        self.total_winnings = 0

        # Auction stats
        self.winning_bid = 0
        self.payout = 0

        # Screen states
        self.next_screen_dict = {"dummy": "pushtostartscreen", 
                                 "pushtostartscreen": "numpad", 
                                 "numpad": "survey",
                                 "continuewalkingscreen": "numpad",
                                 "startwalkingscreen": "pushtostartscreen",
                                 "stopwalkingscreen": "numpad",
                                 "continuesittingscreen": "numpad"
                                 }

    def determine_auction(self):
        # Get bid as float
        # no_bid = not self.sm.bid
        # no_prev_bid = not self.sm.previous_bid
        # if not self.sm.bid:
        #     # If no bid, default to previous bid
        #     subject_bid = float(self.sm.previous_bid) * 0.01
        # else:
        #     subject_bid = float(self.sm.bid) * 0.01

        no_bid = not self.sm.bid
        no_prev_bid = not self.sm.previous_bid
        # Convert bid from string to float
        if not no_bid:
            subject_bid = float(self.sm.bid) * 0.01
        elif not no_prev_bid:
            subject_bid = float(self.sm.previous_bid) * 0.01
            self.sm.bid = self.sm.previous_bid
        else:
            subject_bid = 0

        # Clamp bid
        subject_bid = max(min(subject_bid, MAX_BID), 0)

        # Get all bids from subject/robobidders
        all_bids = [subject_bid]
        all_bids.extend(self.robomodel.get_bids())

        print("asdf", all_bids)
        # Get winner
        ordered_bids = sorted(all_bids)
        self.winning_bid = ordered_bids[0]
        winning_bid_idx = all_bids.index(self.winning_bid)

        # Get payout (Second price)
        self.payout = ordered_bids[1] 

        # Find if subject won
        if winning_bid_idx == 0:
            state = True
            self.total_winnings += self.payout
        else:
            state = False
            robo_walk_time = ROBOWALK_DUR * (self.auction_tally + 1)
            self.robomodel.robobidderlist[winning_bid_idx-1].walk(robo_walk_time, 0)

        # Update auction states
        self.prev_state = self.state
        self.state = state

        # Auction logging values
        t = (self.auction_tally + 1) * ROBOWALK_DUR

        # Send auction results to auctionhouse
        self.sm.callergrpc.call(t, subject_bid, self.state, self.payout, self.total_winnings) #, winning_bid)

        # Increment auction tally
        self.auction_tally += 1

    def close_survey(self):
        t = self.auction_tally * ROBOWALK_DUR
        print("Closing survey", t, self.sm.enjoyment, self.sm.rpe)
        self.sm.callergrpc.question(t, self.sm.enjoyment, self.sm.rpe)

    def send_treadmill_msg(self, state):
        self.sm.callergrpc.treadmill_message(state)

    def next_screen(self, *vargs):
        # Ignore vargs. exists so next can be called by Clock.schedule_once
        self.sm.current = self.next_screen_dict[self.sm.current]