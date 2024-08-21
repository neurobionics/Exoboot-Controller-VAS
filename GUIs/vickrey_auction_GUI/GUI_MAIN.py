import numpy as np
from functools import partial

import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.uix.image import Image, AsyncImage
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty

import grpc
import auction_pb2 as pb2
import auction_pb2_grpc as pb2_grpc

from constants import *
from auction_schedules import *
from statemachine import VA_StateMachine

# Button Callbacks
def numpad_cb(instance):
    print("{} button was pushed".format(instance.val))
    sm = instance.parent.parent
    sm.bid += instance.val
    sm.bid_input.text = decimal_format(sm.bid)

def BCKSPC_CB(instance):
    sm = instance.parent.parent
    sm.bid = sm.bid[:-1]
    sm.bid_input.text = decimal_format(sm.bid)

def CLEAR_CB(instance):
    sm = instance.parent.parent
    sm.bid = ''
    sm.bid_input.text = decimal_format(sm.bid)

def startbttn_CB(instance):
    sm = instance.parent.parent
    if sm.statemachine.auction_tally > 0:
        sm.statemachine.send_treadmill_msg(sm.statemachine.state)
    sm.statemachine.next_screen()

def enjoyment_cb(instance):
    sm = instance.parent.parent
    sm.enjoyment = instance.val
    print("Enjoyment level: {}".format(sm.enjoyment))

def rpe_cb(instance):
    sm = instance.parent.parent
    sm.rpe = instance.val
    print("RPE: {}".format(sm.rpe))

# Numpad screen builder
def buildNumPadScreen(sm):
    screen_ = Screen(name="numpad")
    screen_.sm = sm

    # Grid num
    gn_x = 4
    gn_y = 6

    bid_input = Label(text=decimal_format(sm.bid), font_size='100', size_hint=(4/gn_x, 1/gn_y), pos_hint={'x':0/gn_x, 'y':4/gn_y},  color =(0.5, 0.5, 0.5, 1))
    sm.bid_input = bid_input

    btn0 = Button(text="0", font_size='70', size_hint=(3/gn_x, 1/gn_y), pos_hint={'x':0/gn_x, 'y':0/gn_y},  background_color =(0.5, 0.5, 0.5, 1))
    btn0.val = '0'
    btn0.bind(on_press=numpad_cb)
    
    btnBCKSPC = Button(text="BCKSPC", font_size='70', size_hint=(1/gn_x, 2/gn_y), pos_hint={'x':3/gn_x, 'y':2/gn_y},  background_color =(0.5, 0.5, 0.5, 1))
    btnBCKSPC.bind(on_press=BCKSPC_CB)
    
    btnCLEAR = Button(text="CLEAR", font_size='70', size_hint=(1/gn_x, 2/gn_y), pos_hint={'x':3/gn_x, 'y':0/gn_y},  background_color =(0.5, 0.5, 0.5, 1))
    btnCLEAR.bind(on_press=CLEAR_CB)

    sm.cdt = CountDownTimer(text='', font_size = '70', size_hint=(1/gn_x, 3/gn_y), pos_hint={'x':3/gn_x, 'y':4/gn_y})
    
    timerlabel = Label(text='Close in: ', font_size = '50',size_hint=(1/gn_x, 3/gn_y), pos_hint={'x':2/gn_x, 'y':4/gn_y})

    screen_.add_widget(bid_input)
    screen_.add_widget(btn0)
    screen_.add_widget(btnBCKSPC)
    screen_.add_widget(btnCLEAR)
    screen_.add_widget(sm.cdt)
    screen_.add_widget(timerlabel)

    for i in range(1, 10):
        x_p = ((i-1) % 3) / gn_x
        y_p = ((i-1) // 3 + 1) / gn_y

        btn = Button(text="{}".format(i), font_size='70', size_hint=(1/gn_x, 1/gn_y), pos_hint={'x':x_p, 'y':y_p},  color=(1,1,1), background_color=(0.5,0.5,0.5))
        btn.val = '{}'.format(i)
        btn.bind(on_press=numpad_cb)

        screen_.add_widget(btn)

    screen_.on_enter = partial(numpad_schedule,sm)

    return screen_

def buildsurveyscreen(sm):
    screen_ = Screen(name="survey")
    screen_.sm = sm

    enjoyment_label = Label(text="Rate your enjoyment", font_size='30', size_hint=(1/3, 1/6), pos_hint={'x':1/3, 'y':8.5/10}, halign='center')
    screen_.add_widget(enjoyment_label)

    enjoyment_levels = ['skull', 'frown', 'neutral', 'smile', 'sunglasses']
    for i, level in enumerate(enjoyment_levels):
        btn_ = Button(background_normal='images/{}.png'.format(level), size_hint=(1/6, 1/6), pos_hint={'x':i/5, 'y':2/3})
        btn_.val = i - 2
        btn_.bind(on_press=enjoyment_cb)
        screen_.add_widget(btn_)

    rpe_label = Label(text="Rate your exertion (RPE)", font_size='30', size_hint=(1/3, 1/6), pos_hint={'x':1/3, 'y':1/3}, halign='center')
    screen_.add_widget(rpe_label)

    for i in range(6, 21):
        i_ = i-6
        x_p = i_ / 15
        y_p = 0.1

        btn = Button(text="{}".format(i), font_size='70', color = (1,1,1), background_normal='', background_color= (i_/14,(1-i_/14),0,0.5), size_hint=(1/15, 1/5), pos_hint={'x':x_p, 'y':y_p})
        btn.val = i
        btn.bind(on_press=rpe_cb)
        screen_.add_widget(btn)

    screen_.on_enter = partial(survey_schedule,sm)

    return screen_

# Timer class
class CountDownTimer(Label):
    dur = NumericProperty(0)
    def start(self, dur, *vargs):
        self.dur = dur
        Animation.cancel_all(self)
        self.anim = Animation(dur=0, duration=self.dur)
        def finish_callback(animation, CDT):
            CDT.text = "Finished"
        self.anim.bind(on_complete=finish_callback)
        self.anim.start(self)

    def on_dur(self, instance, value):
        self.text = '{:.2f}'.format(value)

# GRPC object
class CallerGRPC:
    def __init__(self):
        self.channel = grpc.insecure_channel(SERVER_IP)
        self.stub = pb2_grpc.auctionStub(self.channel)
        self.testconnection()

    def testconnection(self):
        # Send testmsg to AuctionHouse
        msg = pb2.testmsg(msg="Hello there")
        response = self.stub.testconnection(msg)
        
        # See response received
        if response:
            print("Connection Successful\n")
        else:
            raise ConnectionError("AuctionHouse connection unsuccessful.")

    def call(self, t, subject_bid, user_win_flag, current_payout, total_winnings):
        resultmsg = pb2.result(t=t,
                         subject_bid=subject_bid,
                         user_win_flag=user_win_flag,
                         current_payout=current_payout,
                         total_winnings=total_winnings
                         )
        response = self.stub.call(resultmsg)
        return response
    
    def question(self, t, enjoyment, rpe):
        surveymsg = pb2.survey(t=t, enjoyment=enjoyment, rpe=rpe)
        response = self.stub.question(surveymsg)
        return response
    
    def treadmill_message(self, state):
        treadmillmsg = pb2.treadmill(state=state)
        response = self.stub.treadmill_message(treadmillmsg)
        return response


# Combines kivy screen manager, statemachine, and GRPC into app
class CallerGUI(App):
    def build(self):
        sm = ScreenManager()
        sm.statemachine = VA_StateMachine(sm)
        sm.callergrpc = CallerGRPC()

        sm.previous_bid = ''
        sm.bid = ''

        # Survey
        sm.enjoyment = 0
        sm.rpe = 0

        label_fontsize = '50'

        # Create Screens
        dummyscreen = Screen(name="dummy")

        pushtostartscreen = Screen(name="pushtostartscreen")
        startbttn = Button(text="Touch to begin", font_size=label_fontsize, color=(1, 1, 1, 1))
        startbttn.bind(on_press=startbttn_CB)
        pushtostartscreen.add_widget(startbttn)

        numpad = buildNumPadScreen(sm)

        survey = buildsurveyscreen(sm)

        # waitingscreen = Screen(name="waitingscreen")
        # waitingscreen.label = Label(text="", color =(1, 1, 1, 1))
        # waitingscreen.add_widget(waitingscreen.label)
        # waitingscreen.on_pre_enter = partial(waitingscreen_pre_enter, waitingscreen, sm)
        # waitingscreen.on_enter = partial(waitingscreen_schedule, sm)

        # Result screens: 4 cases
        sm.continuewalkingscreen = Screen(name="continuewalkingscreen")
        sm.continuewalkingscreen.label = Label(text='', font_size=label_fontsize)
        sm.continuewalkingscreen.add_widget(sm.continuewalkingscreen.label)
        sm.continuewalkingscreen.on_enter = partial(result_screens_schedule, sm)

        sm.startwalkingscreen = Screen(name="startwalkingscreen")
        sm.startwalkingscreen.label = Label(text='', font_size=label_fontsize)
        sm.startwalkingscreen.add_widget(sm.startwalkingscreen.label)
        sm.startwalkingscreen.on_enter = partial(result_screens_schedule, sm)

        sm.stopwalkingscreen = Screen(name="stopwalkingscreen")
        sm.stopwalkingscreen.label = Label(text='', font_size=label_fontsize)
        sm.stopwalkingscreen.add_widget(sm.stopwalkingscreen.label)
        sm.stopwalkingscreen.on_enter = partial(result_screens_schedule, sm)

        sm.continuesittingscreen = Screen(name="continuesittingscreen")
        sm.continuesittingscreen.label = Label(text='', font_size=label_fontsize)
        sm.continuesittingscreen.add_widget(sm.continuesittingscreen.label)
        sm.continuesittingscreen.on_enter = partial(result_screens_schedule, sm)

        # Add screens to ScreenManager
        sm.add_widget(dummyscreen)
        sm.add_widget(pushtostartscreen)
        sm.add_widget(numpad)
        sm.add_widget(survey)
        # sm.add_widget(waitingscreen)
        sm.add_widget(sm.continuewalkingscreen)
        sm.add_widget(sm.startwalkingscreen)
        sm.add_widget(sm.stopwalkingscreen)
        sm.add_widget(sm.continuesittingscreen)

        # Switch from dummy to startscreen to run on_enter
        sm.current = "pushtostartscreen"
        # sm.current = "survey"

        return sm

if __name__ == "__main__":
    CallerGUI().run()
