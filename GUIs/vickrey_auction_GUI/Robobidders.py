import numpy as np

class robobidder():
    # behavior:
        # walk: follows 1st order exponential trend ~ ke^b(t-to)
        # return a bid from 1st order trend

    def __init__(self, k, b): 
        self.k = k
        self.b = b

        # perturbing initial k bid (representing noise in initial biding)
        self.robovalue = self.k + np.random.normal(loc = 0, scale = 0.01) 

    def walk(self, walk_end_time, walk_start_time): 
        self.robovalue = self.k*np.exp(self.b*(walk_end_time - walk_start_time))

    def robobid(self):
         # round bid to 2 decimal places & ...
         # perturb robobid by adding some std (0.01) from normal distribution around '0' - simulates human noise for each bid
        return round(self.robovalue + np.random.normal(loc = 0, scale=0.01), 2)

class roboModel():
    def __init__(self, k, b, num_robobidders): 
        # create a list with num_robobidders elements in it (helps to create instances of 2r/3r bidders)
        self.k = k
        self.b = b
        self.robobidderlist = []
        for i in range (num_robobidders):
            self.robobidderlist.append(robobidder(k, b))

    def get_bids(self):
        return [rb.robobid() for rb in self.robobidderlist] # build list of robobids

    def name(self):
        modelName = "k: {:.4f}, b: {:.4f}, number of robobidders: {}"
        return modelName.format(self.k, self.b, len(self.robobidderlist))




