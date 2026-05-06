import threading
import time
import json

class EventRecorder:

    def __init__(self):
        self.events = []
        self.lock = threading.Lock()

    def record(self, event_type, **kwargs):
        with self.lock:
            event = {'type' : event_type, 'timestamp' : time.time()}
            event.update(kwargs)
            self.events.append(event)

    def flush(self, filepath):
        # copy event list under lock, then release before writing to disk
        with self.lock:
            events_copy = self.events.copy()
        with open(filepath, 'w') as f:
            json.dump(events_copy, f)