import time
import pytest

from . import zmq_helper


def _call_with_retries(helper, req, timeout_s=20.0):
    resp = None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            resp = helper.call(req)
            break
        except TimeoutError:
            time.sleep(0.25)
        except Exception:
            time.sleep(0.25)
    return resp


def test_modhost_bridge_raw_command(modhost_container):
    """Send a raw command via ZeroMQ and verify we get a response forwarded from mod-host."""
    # modhost_container yields (container_id, cmd_port, fb_port, zmq_cmd_port, zmq_pub_port, zmq_health_port)
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)
    req = {"command": "ping"}
    resp = _call_with_retries(helper, req, timeout_s=20.0)
    helper.close()

    assert resp is not None, f"No response for raw command (container={container_id})"
    # Normalized responses include a success flag
    assert resp.get("success") is True, f"Raw command failed or returned unexpected payload: {resp!r}"
    # Expect some textual reply forwarded from mod-host (raw/status/result)
    assert any(k in resp for k in ("raw", "status", "result")), f"Raw command response missing expected fields: {resp!r}"


def test_modhost_bridge_plugin_get_available_plugins(modhost_container):
    """Call plugin.get_available_plugins and assert we receive a plugins collection."""
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)
    req = {"action": "plugin", "method": "get_available_plugins"}
    resp = _call_with_retries(helper, req, timeout_s=20.0)
    helper.close()

    assert resp is not None, f"No response for plugin.get_available_plugins (container={container_id})"
    assert resp.get("success") is True, f"Plugin request failed: {resp!r}"
    # Plugins may be represented as a dict or list depending on implementation; accept either
    plugins = resp.get("plugins")
    assert plugins is not None and isinstance(plugins, (dict, list)), f"Unexpected plugins payload: {resp!r}"


def test_modhost_bridge_audio_get_buffer_size(modhost_container):
    """Call audio.get_jack_buffer_size and verify a numeric buffer_size is returned."""
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)
    req = {"action": "audio", "method": "get_jack_buffer_size"}
    resp = _call_with_retries(helper, req, timeout_s=20.0)
    helper.close()

    assert resp is not None, f"No response for audio.get_jack_buffer_size (container={container_id})"
    assert resp.get("success") is True, f"Audio request failed: {resp!r}"
    assert "buffer_size" in resp, f"Missing buffer_size in response: {resp!r}"
    assert isinstance(resp["buffer_size"], int), f"buffer_size is not integer: {resp!r}"
