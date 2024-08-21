from functools import partial

from kivy.clock import Clock

from constants import *


def numpad_schedule(sm):
    # Reset numpad bid variables on enter
    sm.previous_bid = sm.bid
    sm.bid = ''
    sm.bid_input.text = decimal_format(sm.bid)

    Clock.schedule_once(partial(bidding_open_event,sm), BIDDING_OPEN)
    Clock.schedule_once(partial(cdt_start_event,sm, BIDDING_CLOSE-BIDDING_OPEN), BIDDING_OPEN)
    Clock.schedule_once(partial(bidding_close_event,sm), BIDDING_CLOSE)

def bidding_open_event(sm, dt):
    print("Enter your bids. Auction closes in 60 seconds...")
    pass

def cdt_start_event(sm, dur, dt):
    sm.cdt.start(dur)

def bidding_close_event(sm, dt):
    print("Bidding has been closed! Determining results...")
    sm.statemachine.determine_auction()
    sm.statemachine.next_screen()


# def waitingscreen_pre_enter(waitingscreen, sm):
#     waitingscreen.label.text = "waitingscreen\nstate: {}\nprev_state: {}".format(sm.statemachine.state, sm.statemachine.prev_state)

# def waitingscreen_schedule(sm):
#     Clock.schedule_once(partial(display_result_event,sm), RESULT_SHOW-BIDDING_CLOSE)

def survey_schedule(sm):
    Clock.schedule_once(partial(display_result_event,sm), RESULT_SHOW-BIDDING_CLOSE)

def display_result_event(sm, dt):
    sm.statemachine.close_survey()

    state = sm.statemachine.state
    prev_state = sm.statemachine.prev_state
    
    if state and prev_state:
        sm.current = "continuewalkingscreen"
    if state and not prev_state:
        sm.current = "startwalkingscreen"
    if not state and prev_state:
        sm.current = "stopwalkingscreen"
    if not state and not prev_state:
        sm.current = "continuesittingscreen"


def result_screens_schedule(sm):
    Clock.schedule_once(partial(result_screen_text_event,sm), 0)
    Clock.schedule_once(partial(result_screens_event,sm), AUCTION_CLOSE - RESULT_SHOW)

def result_screen_text_event(sm, dt):
    state = sm.statemachine.state
    screen = sm.current
    print(screen, state)
    if screen == 'continuewalkingscreen':
        sm.continuewalkingscreen.label.text="You have won! Continue Walking.\nWinning Bid: ${:.2f}.\nPayout: ${:.2f}".format(sm.statemachine.winning_bid, sm.statemachine.payout)
        sm.continuewalkingscreen.label.color =(0, 1, 0, 1)
    if screen == 'startwalkingscreen':
        sm.startwalkingscreen.label.text = "You have won! Step on treadmill to begin walking.\nWinning Bid: {:.2f}.\nPayout: {:.2f}".format(sm.statemachine.winning_bid, sm.statemachine.payout)
        sm.startwalkingscreen.label.color =(0, 1, 0, 1)
    if screen == "stopwalkingscreen":
        sm.stopwalkingscreen.label.text = "You have lost. Step off treadmill to sit out the round.\nWinning Bid: {:.2f}.\nPayout: {:.2f}".format(sm.statemachine.winning_bid, sm.statemachine.payout)
        sm.stopwalkingscreen.label.color =(1, 0, 0, 1)
    if screen =="continuesittingscreen":
        sm.continuesittingscreen.label.text = "You have lost. Continue Sitting. Winning Bid:\n{:.2f}.\nPayout: {:.2f}".format(sm.statemachine.winning_bid, sm.statemachine.payout)
        sm.continuesittingscreen.label.color =(1, 0, 0, 1)

def result_screens_event(sm, dt):
    state = sm.statemachine.state
    prev_state = sm.statemachine.prev_state
    if not state and prev_state:
        sm.statemachine.send_treadmill_msg(state)
    sm.statemachine.next_screen()
