from abc import ABC, abstractmethod
import threading
import time

class BaseDetector(ABC):

    def __init__(self, node, event_recorder, check_interval):
        self.node = node
        self.event_recorder = event_recorder
        self.check_interval = check_interval
        # keyed by (host, port), stores timestamp of most recent heartbeat per peer
        self.last_seen = {}
        self.running = False
        # protects last_seen and suspected since on_heartbeat and check_failures run in different threads
        self.lock = threading.Lock()
        # tracks peers currently declared failed; removal is handled here on recovery
        self.suspected = set()


    def on_heartbeat(self, host, port):
        with self.lock:
            self.last_seen[(host, port)] = time.time()

            if (host, port) in self.suspected:
                self.suspected.remove((host, port))
                # NODE_RECOVERED recorded inside the lock; HEARTBEAT_RECEIVED recorded outside it
                self.event_recorder.record('NODE_RECOVERED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

        self.event_recorder.record('HEARTBEAT_RECEIVED', peer_host=host, peer_port=port, detector=self.__class__.__name__)

    @abstractmethod
    def check_failures(self):
        pass

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._check_loop, daemon=True)
        thread.start()

    def _check_loop(self):
        while self.running:
            self.check_failures()
            time.sleep(self.check_interval)

    def stop(self):
        self.running = False