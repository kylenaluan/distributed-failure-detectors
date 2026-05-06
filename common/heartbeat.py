import threading
import socket
import time
import json

class HeartbeatSender(threading.Thread):

    def __init__(self, node, interval, simulator=None):
        super().__init__()
        self.node = node
        self.interval = interval
        self.running = False
        self.daemon = True
        self.simulator = simulator
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        self.running = True

        while self.running:
            for peer in self.node.get_peers():
                self._send(peer)
            time.sleep(self.interval)

    def _send(self, peer):
        try:
            # encode sender's host and port so the receiver can identify the source
            message = json.dumps({"host": self.node.host, "port": self.node.port})
            message_bytes = message.encode("utf-8")
            # route through simulator if present, otherwise send directly
            if self.simulator:
                self.simulator.send(message_bytes, self.node.host, self.node.port, peer)
            else:
                self.sock.sendto(message_bytes, (peer.host, peer.port))

        except Exception:
            pass

    def stop(self):
        self.running = False
        self.sock.close()

class HeartbeatListener(threading.Thread):

    def __init__(self, node, on_heartbeat):
        super().__init__()
        self.node = node
        self.on_heartbeat = on_heartbeat
        self.running = False
        self.daemon = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # timeout prevents recvfrom from blocking forever so the loop can exit cleanly
        self.sock.settimeout(1.0)
        self.sock.bind((self.node.host, self.node.port))

    def run(self):
        self.running = True

        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode("utf-8"))
                self.on_heartbeat(message['host'], message['port'])

            except socket.timeout:
                pass

            except Exception:
                pass

    def stop(self):
        self.running = False
        self.sock.close()
