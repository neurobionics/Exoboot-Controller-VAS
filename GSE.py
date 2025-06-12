from src.exo.gait_state_estimator.forceplate.ZMQ_PubSub import Subscriber

from GSE_Bertec import Bertec_Estimator

from src.settings.constants import VICON_IP


class GSE:
    def __init__(self, topics=["fz_left", "fz_right"], publisher_ip=VICON_IP, timeout_ms=5, stride_period_init=1.2, filter_size=10, hs_threshold = 80, to_threshold = 30):
        self.topics = topics

        self.subscribers = {}
        self.estimators = {}

        for topic in self.topics:
            self.subscribers[topic] = Subscriber(publisher_ip=publisher_ip, topic_filter=topic, timeout_ms=timeout_ms)
            self.estimators[topic] = Bertec_Estimator(self.subscribers[topic], stride_period_init=stride_period_init, filter_size=filter_size, hs_threshold=hs_threshold, to_threshold=to_threshold)

    def link_to_exoboot(self, exoboot):
        pass

    def update(self):
        for estimator in self.estimators.values():
            estimator.update()
