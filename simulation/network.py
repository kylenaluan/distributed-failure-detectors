import socket
import threading
import time
import random

class NetworkSimulator:

    def __init__(self, loss_rate=0.0, delay=0.0, jitter=0.0):
        self.loss_rate = loss_rate
        self.delay = delay
        self.jitter = jitter
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data, src_host, src_port, peer):
        with self.lock:
            loss_rate = self.loss_rate
            delay = self.delay
            jitter = self.jitter

        # random packet loss based on loss_rate
        if random.random() < loss_rate:
            return

        # compute total sleep time from delay and jitter
        # sleep for that total duration
        total_delay = delay + random.uniform(0, jitter)
        time.sleep(total_delay)

        # send packet to peer
        try:
            self.sock.sendto(data, (peer.host, peer.port))
        except Exception:
            pass

    def set_loss_rate(self, loss_rate):
        with self.lock:
            self.loss_rate = loss_rate

    def set_delay(self, delay):
        with self.lock:
            self.delay = delay

    def set_jitter(self, jitter):
        with self.lock:
            self.jitter = jitter