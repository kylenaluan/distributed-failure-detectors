from detectors import BaseDetector
import time

class FixedTimeoutDetector(BaseDetector):

    def __init__(self, node, event_recorder, check_interval, timeout):
        super().__init__(node, event_recorder, check_interval)
        self.timeout = timeout            

    def check_failures(self):
        current_time = time.time()
        # copy last_seen under lock then iterate the copy to keep lock held for minimum duration
        with self.lock:
            last_seen_copy = self.last_seen.copy()

        for (host, port), last_time in list(last_seen_copy.items()):
            # suspected guard prevents repeated FAILURE_DETECTED events after the first timeout
            if current_time - last_time > self.timeout and (host, port) not in self.suspected:
                self.event_recorder.record('FAILURE_DETECTED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

                with self.lock:
                    self.suspected.add((host, port))