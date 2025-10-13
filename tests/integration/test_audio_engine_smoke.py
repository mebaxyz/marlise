import os
import time
import socket
import re
import pytest

from . import docker_helpers
from . import zmq_helper


def _run_container_with_modhost(tag: str, stage: str):
    # Delegate to centralized helper for a short-lived smoke run
    return docker_helpers.run_container_with_modhost(tag, stage)


def test_modhost_smoke(modhost_image_tag):
    tag, stage = modhost_image_tag
    res = _run_container_with_modhost(tag, stage)
    out = res.stdout.decode(errors="ignore")
    assert res.returncode == 0, f"mod-host smoke command failed: exit={res.returncode}\n{out}"
    assert "mod-host" in out.lower() or "version" in out.lower()


# Note: container start/port discovery is centralized in tests/integration/docker_helpers.py


def test_modhost_ping_socket(modhost_container):
    # modhost_container now yields (container_id, host_port, host_port_fb, host_port_zmq)
    container_id, host_port, host_port_fb, _host_port_zmq = modhost_container

    # Try to connect command and feedback sockets, then send a ping and read
    # response. Both sockets must be connected before sending commands.
    received = None
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", host_port), timeout=3) as cmd_sock:
                with socket.create_connection(("127.0.0.1", host_port_fb), timeout=3) as fb_sock:
                    cmd_sock.settimeout(3.0)
                    fb_sock.settimeout(1.0)

                    # send null-terminated ping per README smoke test
                    cmd_sock.sendall(b"ping\x00")

                    # Read from command socket until null terminator or timeout
                    chunks = []
                    read_deadline = time.time() + 3.0
                    while time.time() < read_deadline:
                        try:
                            chunk = cmd_sock.recv(4096)
                        except socket.timeout:
                            break
                        if not chunk:
                            break
                        chunks.append(chunk)
                        if b"\x00" in chunk:
                            break

                    if chunks:
                        received = b"".join(chunks)
                        break
        except (ConnectionRefusedError, TimeoutError, OSError):
            time.sleep(0.25)
    assert received is not None, f"No response from mod-host command port after retries (container={container_id})"
    # Expect a null-terminated resp message, e.g. b'resp 0\x00'
    assert b"resp" in received.lower(), f"Unexpected response from mod-host: {received!r}"


def test_modhost_bridge_health(modhost_container):
    """Verify the modhost-bridge ZeroMQ health endpoint responds as expected."""
    # modhost_container yields (container_id, cmd_port, fb_port, zmq_cmd_port, zmq_pub_port, zmq_health_port)
    container_id, _cmd_port, _fb_port, host_port_zmq, host_port_pub, host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_health, timeout_ms=3000)
    req = {"action": "health"}
    resp = None
    deadline = time.time() + 20.0
    while time.time() < deadline:
        try:
            resp = helper.call(req)
            break
        except TimeoutError:
            time.sleep(0.25)
        except Exception:
            # unexpected error, retry a few times
            time.sleep(0.25)

    helper.close()

    assert resp is not None, "No response from modhost-bridge health endpoint after timeout"
    assert isinstance(resp, dict), f"Unexpected health response type: {type(resp)}"
    assert resp.get("status") in ("healthy", "starting", "degraded", "unhealthy"), "Invalid health status"


def test_modhost_bridge_list_plugins(modhost_container):
    """Call plugin manager list_instances/list_plugins and assert we get a JSON list."""
    container_id, _cmd_port, _fb_port, host_port_zmq, host_port_pub, host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)
    req = {"action": "plugin", "method": "list_instances"}
    resp = None
    deadline = time.time() + 20.0
    while time.time() < deadline:
        try:
            resp = helper.call(req)
            break
        except TimeoutError:
            time.sleep(0.25)
        except Exception:
            time.sleep(0.25)

    helper.close()

    assert resp is not None, "No response from modhost-bridge list_instances after timeout"
    assert isinstance(resp, (dict, list)), f"Unexpected list_instances response: {resp!r}"
