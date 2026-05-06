from collections import namedtuple

Peer = namedtuple('Peer', ['host', 'port'])

class Node:

    def __init__(self, node_id, host, port, peers=None):
        self.node_id = node_id
        self.host = host
        self.port = port
        if peers is not None:
            self.peers = peers
        else:
            self.peers = []

    # Add a new peer to node list
    def add_peer(self, host, port):
        new_peer = Peer(host, port)

        # Check for duplicate peers
        if new_peer not in self.peers:
            self.peers.append(new_peer)

    def get_peers(self):
        return self.peers
    
    def __repr__(self):
        return f'Node {self.node_id} - ({self.host}:{self.port})'