from detectors.base import BaseDetector
from collections import deque
from statistics import NormalDist
import numpy as np
import math
import time

class PhiAccrualDetector(BaseDetector):

    def __init__(self, node, event_recorder, check_interval, threshold, window_size):
        super().__init__(node, event_recorder, check_interval)
        self.threshold = threshold
        self.window_size = window_size
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

    def _compute_phi(self, t, mean, std_dev):
        # clamp std_dev to avoid division by zero when all intervals are identical
        std_dev = max(std_dev, 1e-6)
        cdf = NormalDist(mu=mean, sigma=std_dev).cdf(t)
        p_later = 1 - cdf
        # clamp p_later to avoid log10(0)
        p_later = max(p_later, 1e-10)
        return -math.log10(p_later)

    def check_failures(self):
        current_time = time.time()
        with self.lock:
            last_seen_copy = self.last_seen.copy()

        for (host, port), last_time in list(last_seen_copy.items()):
            if (host, port) in self.suspected:
                continue

            # skip peers without enough samples to fit the distribution
            if (host, port) not in self.intervals or len(self.intervals[(host, port)]) < 10:
                continue

            intervals_array = np.array(self.intervals[(host, port)])
            mean = np.mean(intervals_array)
            std_dev = np.std(intervals_array)
            t = current_time - last_time
            phi = self._compute_phi(t, mean, std_dev)

            if phi > self.threshold:
                self.event_recorder.record('FAILURE_DETECTED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

                with self.lock:
                    self.suspected.add((host, port))