import time
import pytest

from . import zmq_helper


def test_modhost_bridge_unhealthy_to_healthy(modhost_container):
    """If the bridge starts unhealthy, verify it becomes healthy within a timeout.

    Accepts the case where the bridge is already healthy at first probe.
    """
    # modhost_container yields (container_id, cmd_port, fb_port, zmq_cmd_port, zmq_pub_port, zmq_health_port)
    container_id, _cmd, _fb, _zmq_cmd, _zmq_pub, host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_health, timeout_ms=3000)
    req = {"action": "health"}

    # Get an initial health response (allow up to 20s for startup)
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

    assert resp is not None, "No initial health response from modhost-bridge"
    assert isinstance(resp, dict), f"Unexpected health response type: {type(resp)}"

    status = resp.get("status")
    # If already healthy, test is satisfied
    if status == "healthy":
        helper.close()
        return

    # Otherwise, wait up to 30s for status to become healthy
    became_healthy = False
    deadline2 = time.time() + 30.0
    last_resp = resp
    while time.time() < deadline2:
        try:
            r = helper.call(req)
            last_resp = r
            if isinstance(r, dict) and r.get("status") == "healthy":
                became_healthy = True
                break
        except TimeoutError:
            pass
        except Exception:
            pass
        time.sleep(0.25)

    helper.close()

    assert became_healthy, (
        f"Bridge did not transition to 'healthy' within timeout (container={container_id}). Last response: {last_resp!r}"
    )
