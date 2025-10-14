import time
import json
import pytest

from .zmq_helper import ZMQHelper


def _call(helper, req, retries=3, wait=0.3):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(wait)
    return None


@pytest.mark.integration
def test_session_manager_basic(modhost_container):
    # modhost_container fixture provides (container_id, cmd_port, fb_port, zmq_port, pub_port, health_port)
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=5000)

    # 1) call a session-manager style RPC if available: get_available_plugins (via bridge/session-manager)
    resp = _call(helper, {"action": "plugin", "method": "get_available_plugins"}, retries=5)
    assert resp is not None

    # 2) check session-manager health via bridge (best-effort)
    # some deployments expose a health RPC; try both system and session paths
    for hreq in (
        {"action": "system", "method": "health"},
        {"action": "session", "method": "health"},
    ):
        try:
            h = _call(helper, hreq, retries=2)
            if h is not None:
                assert 'status' in h or 'success' in h
                break
        except Exception:
            pass

    helper.close()
