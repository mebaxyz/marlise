import zmq
import json


class ZMQHelper:
    def __init__(self, host: str = "127.0.0.1", port: int = 6000, timeout_ms: int = 3000):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.timeout_ms = int(timeout_ms)
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)
        self.endpoint = f"tcp://{host}:{port}"
        self.sock.connect(self.endpoint)

    def call(self, obj: dict):
        """Send a JSON object and wait for JSON response or raise TimeoutError."""
        self.sock.send_json(obj)
        socks = dict(self.poller.poll(self.timeout_ms))
        if socks.get(self.sock) != zmq.POLLIN:
            raise TimeoutError("No response from ZeroMQ endpoint")
        return self.sock.recv_json()

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass
