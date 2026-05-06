from detectors.base import BaseDetector
from collections import deque
from statistics import NormalDist
import numpy as np
import math
import time

class ConfidenceIntervalDetector(BaseDetector):

    def __init__(self, node, event_recorder, check_interval, threshold, window_size, confidence_level):
        super().__init__(node, event_recorder, check_interval)
        self.threshold = threshold
        self.window_size = window_size
        # compute z-score once from confidence level (e.g. 0.95 -> 1.96)
        self.z_score = NormalDist().inv_cdf((1 + confidence_level) / 2)
        self.intervals = {}

    def on_heartbeat(self, host, port):
        prev_time = self.last_seen.get((host, port))
        # capture timestamp once before super() overwrites last_seen
        now = time.time()
        super().on_heartbeat(host, port)

        if prev_time is not None:
            # use captured timestamp to calculate interval
            interval = now - prev_time
            with self.lock:
                if (host, port) not in self.intervals:
                    self.intervals[(host, port)] = deque(maxlen=self.window_size)
                self.intervals[(host, port)].append(interval)

    def check_failures(self):
        with self.lock:
            last_seen_copy = self.last_seen.copy()

        for (host, port) in list(last_seen_copy):
            if (host, port) in self.suspected:
                continue

            # skip peers without enough samples to compute a meaningful interval
            if (host, port) not in self.intervals or len(self.intervals[(host, port)]) < 2:
                continue

            intervals_array = np.array(self.intervals[(host, port)])
            mean = np.mean(intervals_array)
            std_dev = np.std(intervals_array)
            n = len(intervals_array)
            # lower bound is the most optimistic estimate of the true mean gap
            lower_bound = mean - (self.z_score * std_dev / math.sqrt(n))

            # declare failure only when even the optimistic estimate exceeds the threshold
            if lower_bound > self.threshold:
                self.event_recorder.record('FAILURE_DETECTED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

                with self.lock:
                    self.suspected.add((host, port))