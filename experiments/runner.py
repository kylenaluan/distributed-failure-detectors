import threading
import time
import random
from pathlib import Path

from common import Node
from common import HeartbeatSender, HeartbeatListener
from common import EventRecorder

from simulation import NetworkSimulator
from simulation import FaultInjector

from detectors import FixedTimeoutDetector
from detectors import AdaptiveTimeoutDetector
from detectors import PhiAccrualDetector
from detectors import ConfidenceIntervalDetector


class ExperimentRunner:

    def __init__(self, scenario, config, node_id):
        self.scenario = scenario
        self.config = config
        # node_id identifies which node this process is running as
        self.node_id = node_id

        # heartbeat parameters
        self.heartbeat_interval = config['heartbeat']['interval']
        self.check_interval = config['heartbeat']['check_interval']

        # detector parameters
        self.fixed_timeout = config['detectors']['fixed_timeout']['timeout']

        self.adaptive_default = config['detectors']['adaptive_timeout']['default_timeout']
        self.adaptive_k = config['detectors']['adaptive_timeout']['k']
        self.adaptive_window = config['detectors']['adaptive_timeout']['window_size']

        self.phi_threshold = config['detectors']['phi_accrual']['threshold']
        self.phi_window = config['detectors']['phi_accrual']['window_size']

        self.confidence_threshold = config['detectors']['confidence_interval']['threshold']
        self.confidence_window = config['detectors']['confidence_interval']['window_size']
        self.confidence_level = config['detectors']['confidence_interval']['confidence_level']

        # log directory
        self.log_dir = Path(config['logs']['directory'])

        # populated in run()
        self.node = None
        self.senders = {}
        self.simulator = None
        self.injector = None

    def _build_this_node(self):
        # find this node's own config entry by node_id
        own_config = next(n for n in self.config['nodes'] if n['node_id'] == self.node_id)
        node = Node(own_config['node_id'], own_config['host'], own_config['port'])

        # add all other nodes as peers
        for peer_config in self.config['nodes']:
            if peer_config['node_id'] != self.node_id:
                node.add_peer(peer_config['host'], peer_config['port'])

        return node

    def _build_detectors(self, node, event_recorder):
        detectors = {}

        detectors['FixedTimeout'] = FixedTimeoutDetector(node, event_recorder, self.check_interval, self.fixed_timeout)
        detectors['AdaptiveTimeout'] = AdaptiveTimeoutDetector(node, event_recorder, self.check_interval, self.adaptive_default, self.adaptive_k, self.adaptive_window)
        detectors['PhiAccrual'] = PhiAccrualDetector(node, event_recorder, self.check_interval, self.phi_threshold, self.phi_window)
        detectors['ConfidenceInterval'] = ConfidenceIntervalDetector(node, event_recorder, self.check_interval, self.confidence_threshold, self.confidence_window, self.confidence_level)

        return detectors

    def _schedule_fault_events(self, event_recorder):
        for event in self.scenario.fault_events:
            timer = threading.Timer(
                event.time_offset,
                self._make_fault_callback(event, event_recorder)
            )
            timer.start()

    def _dispatch_fault(self, event, event_recorder):
        if event.action == 'crash':
            # only crash this node's sender if this node is the target
            if event.params['node_id'] == self.node_id:
                self.injector.crash(self.node)
                event_recorder.record('NODE_CRASHED', node=self.node_id)

        elif event.action == 'recover':
            # only recover this node's sender if this node is the target
            if event.params['node_id'] == self.node_id:
                self.injector.recover(self.node)
                event_recorder.record('NODE_RECOVERED', node=self.node_id)

        elif event.action == 'set_congestion':
            # congestion affects all outgoing traffic regardless of target node
            self.injector.set_congestion(**event.params)
            event_recorder.record('CONGESTION_START', **event.params)

        elif event.action == 'clear_congestion':
            # congestion clear affects all outgoing traffic regardless of target node
            self.injector.clear_congestion()
            event_recorder.record('CONGESTION_END')

    def _make_fault_callback(self, event, event_recorder):
        def callback():
            self._dispatch_fault(event, event_recorder)
        return callback

    def _make_detector_callback(self, detectors):
        def on_heartbeat(host, port):
            for detector in detectors.values():
                detector.on_heartbeat(host, port)
        return on_heartbeat

    def run(self):
        random.seed(self.scenario.seed)

        # build and start only this node
        self.node = self._build_this_node()
        self.simulator = NetworkSimulator()
        event_recorder = EventRecorder()

        # build and start detectors for this node
        detectors = self._build_detectors(self.node, event_recorder)
        for detector in detectors.values():
            detector.start()

        # build and start listener and sender for this node
        listener = HeartbeatListener(self.node, self._make_detector_callback(detectors))
        sender = HeartbeatSender(self.node, self.heartbeat_interval, self.simulator)
        listener.start()
        sender.start()

        # fault injector only manages this node's sender
        self.senders[self.node_id] = sender
        self.injector = FaultInjector(self.senders, self.simulator, self.heartbeat_interval)

        # schedule fault events — each node filters for its own
        self._schedule_fault_events(event_recorder)

        # block until scenario is over
        time.sleep(self.scenario.duration)

        # stop all threads
        for detector in detectors.values():
            detector.stop()
        listener.stop()
        sender.stop()

        # flush logs
        self.log_dir.mkdir(parents=True, exist_ok=True)
        scenario_name = self.scenario.name.replace(' ', '_')
        event_recorder.flush(self.log_dir / f"{scenario_name}_{self.node_id}_events.json")