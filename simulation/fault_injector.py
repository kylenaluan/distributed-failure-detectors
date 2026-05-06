from common import HeartbeatSender

class FaultInjector:

    def __init__(self, senders, simulator, interval):
        self.senders = senders
        self.simulator = simulator
        self.interval = interval

    def crash(self, node):
        # stop the HeartbeatSender for this node
        self.senders[node.node_id].stop()

    def recover(self, node):
        # create a brand new HeartbeatSender for this node
        sender = HeartbeatSender(node, self.interval, self.simulator)
        sender.start()
        self.senders[node.node_id] = sender

    def set_congestion(self, delay, jitter, loss_rate):
        self.simulator.set_delay(delay)
        self.simulator.set_jitter(jitter)
        self.simulator.set_loss_rate(loss_rate)

    def clear_congestion(self):
        self.simulator.set_delay(0.0)
        self.simulator.set_jitter(0.0)
        self.simulator.set_loss_rate(0.0)