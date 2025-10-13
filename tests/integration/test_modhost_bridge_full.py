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


def _extract_first_plugin_uri(plugins_payload):
    # plugins_payload may be dict (uri->info) or list of PluginInfo
    if plugins_payload is None:
        return None
    if isinstance(plugins_payload, dict):
        for k in plugins_payload.keys():
            return k
    if isinstance(plugins_payload, list) and len(plugins_payload) > 0:
        first = plugins_payload[0]
        if isinstance(first, dict):
            return first.get("uri") or first.get("plugin_uri")
    return None


def test_plugin_lifecycle_and_parameters(modhost_container):
    """Load a plugin (if available), inspect instance, set/get a parameter, then unload."""
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)

    # Get available plugins
    resp = _call_with_retries(helper, {"action": "plugin", "method": "get_available_plugins"})
    assert resp is not None, "No response for get_available_plugins"
    assert resp.get("success") is True
    plugins = resp.get("plugins")
    assert plugins is not None, "plugins payload missing"

    plugin_uri = _extract_first_plugin_uri(plugins)

    if not plugin_uri:
        # Nothing to load; still assert list_instances and return early
        resp_li = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
        assert resp_li is not None and resp_li.get("success") is True
        helper.close()
        pytest.skip("No available plugins found in test image")

    # Try to load the plugin
    load_req = {"action": "plugin", "method": "load_plugin", "uri": plugin_uri}
    resp_load = _call_with_retries(helper, load_req)
    assert resp_load is not None, f"No response loading plugin {plugin_uri}"

    # Normalize: instance_id may be top-level or under 'result' or 'plugin'
    instance_id = resp_load.get("instance_id") or (resp_load.get("result") and resp_load.get("result").get("instance_id"))
    if not instance_id and resp_load.get("plugin") and isinstance(resp_load.get("plugin"), dict):
        instance_id = resp_load.get("plugin").get("instance_id")

    assert instance_id is not None, f"Failed to obtain instance_id after loading plugin: {resp_load!r}"

    # Query plugin info
    info_req = {"action": "plugin", "method": "get_plugin_info", "instance_id": instance_id}
    resp_info = _call_with_retries(helper, info_req)
    assert resp_info is not None and resp_info.get("success") is True
    plugin_info = resp_info.get("plugin") or resp_info.get("result")
    assert plugin_info is not None and isinstance(plugin_info, dict)

    # If plugin reports parameters, try set/get on first parameter
    params = plugin_info.get("parameters") or {}
    first_param = None
    if isinstance(params, dict) and params:
        first_param = next(iter(params.keys()))

    if first_param:
        # set parameter
        set_req = {
            "action": "plugin",
            "method": "set_parameter",
            "instance_id": instance_id,
            "parameter": first_param,
            "value": 0.5,
        }
        resp_set = _call_with_retries(helper, set_req)
        assert resp_set is not None and resp_set.get("success") is True

        # get parameter
        get_req = {"action": "plugin", "method": "get_parameter", "instance_id": instance_id, "parameter": first_param}
        resp_get = _call_with_retries(helper, get_req)
        assert resp_get is not None and resp_get.get("success") is True
        assert "value" in resp_get

    # Unload plugin
    unload_req = {"action": "plugin", "method": "unload_plugin", "instance_id": instance_id}
    resp_unload = _call_with_retries(helper, unload_req)
    assert resp_unload is not None and resp_unload.get("success") is True

    helper.close()


def test_list_instances_and_rescan(modhost_container):
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)

    resp = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
    assert resp is not None and resp.get("success") is True
    instances = resp.get("instances") or resp.get("result") or {}
    assert isinstance(instances, (dict, list))

    # Rescan plugins (should reply with status fields)
    resp_rescan = _call_with_retries(helper, {"action": "plugin", "method": "rescan_plugins"})
    assert resp_rescan is not None and resp_rescan.get("success") is True

    helper.close()


def test_audio_ports_connect_disconnect(modhost_container):
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)

    # Query hardware ports
    resp_ports = _call_with_retries(helper, {"action": "audio", "method": "get_jack_hardware_ports", "is_audio": True, "is_output": False})
    assert resp_ports is not None and resp_ports.get("success") is True
    ports = resp_ports.get("ports") or []
    assert isinstance(ports, list)

    if len(ports) >= 2:
        p1 = ports[0]
        p2 = ports[1]
        # Try connect (may succeed or fail depending on environment); assert response shape
        resp_conn = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": p1, "port2": p2})
        assert resp_conn is not None and resp_conn.get("success") is True

        # Disconnect
        resp_disc = _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": p1, "port2": p2})
        assert resp_disc is not None and resp_disc.get("success") is True

    # buffer size / sample rate queries
    resp_buf = _call_with_retries(helper, {"action": "audio", "method": "get_jack_buffer_size"})
    assert resp_buf is not None and resp_buf.get("success") is True
    assert "buffer_size" in resp_buf

    resp_sr = _call_with_retries(helper, {"action": "audio", "method": "get_jack_sample_rate"})
    assert resp_sr is not None and resp_sr.get("success") is True
    assert "sample_rate" in resp_sr

    helper.close()
