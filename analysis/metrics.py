import json

class MetricsComputer:

    def __init__(self, events, node_map):
        self.events = events
        self.node_map = node_map # used to resolve node_id <-> (host, port)
        self.reverse_node_map = {(host, port): node_id for node_id, (host, port) in node_map.items()} # (host, port) -> node_id
        self._crashes = self._get_crashes()

    def _get_detector_names(self):
        # set of all unique detector names found in events
        detector_names = set()
        for event in self.events:
            if 'detector' in event:
                detector_names.add(event['detector'])
        return detector_names

    def _get_crashes(self):
        # return list of NODE_CRASHED events
        crashes = []
        for event in self.events:
            if event['type'] == 'NODE_CRASHED':
                crashes.append(event)
        return crashes

    def _get_detections(self, detector_name):
        # return list of FAILURE_DETECTED events for a given detector
        failure_detections = []
        for event in self.events:
            if event['type'] == 'FAILURE_DETECTED' and event['detector'] == detector_name:
                failure_detections.append(event)
        return failure_detections

    def _is_true_positive(self, detection_event):
        # map detection_event's peer_host/peer_port to node_id using reverse_node_map
        peer_host = detection_event['peer_host']
        peer_port = detection_event['peer_port']
        peer_id = self.reverse_node_map.get((peer_host, peer_port))

        # unknown peer (not in node_map) - treat as false positive
        if peer_id is None:
            return False

        for crash in self._crashes:
            if crash['node'] == peer_id and crash['timestamp'] < detection_event['timestamp']:
                # check if the node recovered between the crash and the detection
                recovered = False
                for e in self.events:
                    if (e['type'] == 'NODE_RECOVERED'
                            and e.get('node') == peer_id
                            and crash['timestamp'] < e['timestamp'] < detection_event['timestamp']):
                        recovered = True
                        break

                # detection is only valid if the node hasn't recovered since the crash
                if not recovered:
                    return True

        return False
    
    def compute_false_positive_rate(self, detector_name):
        detections = self._get_detections(detector_name)

        # no failure detections - undefined metric
        if len(detections) == 0:
            return None

        # calculate total false positives
        false_positives = 0
        for detection in detections:
            if not self._is_true_positive(detection):
                false_positives += 1

        return false_positives / len(detections)

    def compute_detection_time(self, detector_name):
        # no crashes - undefined metric
        if len(self._crashes) == 0:
            return None

        detections = self._get_detections(detector_name)
        total_time = 0
        count = 0

        for crash in self._crashes:
            host_port = self.node_map.get(crash['node'])

            # skip if crashed node not in node_map
            if host_port is None:
                continue

            host, port = host_port

            # find first detection for this peer after the crash timestamp
            for detection in detections:
                if (detection['peer_host'] == host and
                    detection['peer_port'] == port and
                    detection['timestamp'] > crash['timestamp']):
                        total_time += detection['timestamp'] - crash['timestamp']
                        count += 1
                        break

        # return average detection time, or None if crash was not detected
        if count > 0:
            return total_time / count
        else:
            return None

    def compute_mistake_rate(self, detector_name):
        detections = self._get_detections(detector_name)

        # no events - return None
        if len(self.events) == 0:
            return None

        # calculate experiment duration in minutes
        max_timestamp = max(event['timestamp'] for event in self.events)
        min_timestamp = min(event['timestamp'] for event in self.events)
        duration = (max_timestamp - min_timestamp) / 60

        # error if no time elapsed
        if duration == 0:
            return None

        # calculate false positives
        false_positives = 0
        for detection in detections:
            if not self._is_true_positive(detection):
                false_positives += 1

        return false_positives / duration

    def compute_all(self, detector_name):
        # compute all three metrics for this detector and return as a dict
        return {
            'detector': detector_name,
            'false_positive_rate': self.compute_false_positive_rate(detector_name),
            'detection_time': self.compute_detection_time(detector_name),
            'mistake_rate': self.compute_mistake_rate(detector_name)
        }

    @classmethod
    def from_log_file(cls, filepath, node_map):
        # load events from a JSON log file and return a MetricsComputer instance
        with open(filepath, 'r') as f:
            events = json.load(f)
        return cls(events, node_map)