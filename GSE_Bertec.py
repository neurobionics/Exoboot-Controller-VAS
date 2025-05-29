import time

from src.utils.filter_utils import MovingAverageFilter

class Bertec_Estimator:
    """
    Stride phase estimation using forceplate thresholding
    """
    def __init__(self, zmq_subscriber, stride_period_init=1.2, filter_size=10, hs_threshold = 80, to_threshold = 30):
        # ZMQ subscriber
        self.subscriber = zmq_subscriber

        # Constants
        self.hs_threshold = hs_threshold
        self.to_threshold = to_threshold

        # State variables
        self.HS = 0
        self.TO = 0
        self.force_prev = 0
        self.in_contact = False    # True == in stance

        self.stride_period_tracker = MovingAverageFilter(initial_value=stride_period_init, size=filter_size)

    def return_estimate(self):
        """
        Return a dictionary of the most recent state of estimator {a, b, c}
            a) most recent heel strike time
            b) average stride period
            c) in swing
            
        """
        state_dict = {"HS": self.HS, 
                      "stride_period": self.stride_period_tracker.average(), 
                      "in_swing": not self.in_contact
                      }

        return state_dict

    def update(self):
        """
        Update estimator state with new force data
        Returns (a, b)
            a) if new stride has been observed
            b) force from Bertec
        """

        # ZMQ streaming get message
        topic, force, timestep_valid = self.subscriber.get_message()

        # Catch empty messages
        force = self.force_prev if force == '' else float(force)

        # New stride flag
        new_stride = False

        # Determine state
        if self.in_contact:
            if force < self.to_threshold:
                # New Toe off
                self.in_contact = False
                self.TO = time.time()

            else:
                # In stance
                self.in_contact = True

        else:
            if force >= self.hs_threshold:
                # New Heel strike
                self.in_contact = True
                new_stride = True

                # Record new stride period and update estimate
                HS_new = time.time()
                stride_period_new = HS_new - self.HS
                self.stride_period_tracker.update(stride_period_new)

                self.HS = HS_new

            else:
                # In swing
                self.in_contact = False

        # Update prev
        self.force_prev = force

        return new_stride, force
