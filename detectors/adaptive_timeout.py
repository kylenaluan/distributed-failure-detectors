from detectors import BaseDetector
from collections import deque
import numpy as np
import time

class AdaptiveTimeoutDetector(BaseDetector):

    def __init__(self, node, event_recorder, check_interval, default_timeout, k, window_size):
        super().__init__(node, event_recorder, check_interval)
        self.default_timeout = default_timeout
        self.k = k
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

    def check_failures(self):
        current_time = time.time()
        with self.lock:
            last_seen_copy = self.last_seen.copy()

        for (host, port), last_time in list(last_seen_copy.items()):
            if (host, port) in self.suspected:
                continue

            if (host, port) not in self.intervals or len(self.intervals[(host, port)]) < 10:
                # fall back to default timeout until window is populated
                timeout = self.default_timeout
            else:
                intervals_array = np.array(self.intervals[(host, port)])
                # timeout grows with variance to reduce false positives during congestion
                timeout = np.mean(intervals_array) + self.k * np.std(intervals_array)

            if current_time - last_time > timeout:
                self.event_recorder.record('FAILURE_DETECTED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

                with self.lock:
                    self.suspected.add((host, port))