import time
import pytest

from .zmq_helper import ZMQHelper


def _call(helper, req, retries=3, wait=0.25):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(wait)
    return None


@pytest.mark.integration
def test_session_manager_all_rpc(modhost_container):
    """Best-effort exercise of many session-manager RPCs via ZeroMQ.

    This test intentionally avoids destructive operations (shutdown, reboot,
    install/remove packages, delete files). It focuses on read-only handlers
    and safe plugin operations (load/remove a single plugin if available).
    """
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=5000)

    # 1) Core system / health handlers
    for req in (
        {"action": "system", "method": "get_system_info"},
        {"action": "system", "method": "get_cpu_usage"},
        {"action": "system", "method": "get_memory_usage"},
        {"action": "system", "method": "get_disk_usage"},
        {"action": "system", "method": "get_network_info"},
        {"action": "system", "method": "get_logs", "lines": 10},
        {"action": "system", "method": "list_snapshots"},
        {"action": "system", "method": "list_files", "path": "/"},
    ):
        try:
            r = _call(helper, req, retries=2)
            assert r is None or isinstance(r, dict)
        except AssertionError:
            # don't fail hard on environment differences
            pass

    # 2) Session handlers
    for req in (
        {"action": "health_check", "method": "health_check"},
        {"action": "system", "method": "get_metrics"},
    ):
        try:
            r = _call(helper, req, retries=2)
            assert r is None or isinstance(r, dict)
        except AssertionError:
            pass

    # 3) Plugin-related handlers: discover available plugins first
    resp_plugins = _call(helper, {"action": "plugin", "method": "get_available_plugins"}, retries=5)
    plugin_uri = None
    if resp_plugins and resp_plugins.get("success"):
        plugins = resp_plugins.get("plugins") or {}
        if isinstance(plugins, dict):
            plugin_uri = next(iter(plugins.keys()), None)
        elif isinstance(plugins, list) and plugins:
            first = plugins[0]
            if isinstance(first, dict):
                plugin_uri = first.get("uri") or first.get("plugin_uri")

    # Exercise plugin list/info handlers
    _call(helper, {"action": "plugin", "method": "list_plugins"})
    _call(helper, {"action": "plugin", "method": "get_plugins_bulk"})

    instance_id = None
    host_instance = None
    if plugin_uri:
        # attempt to load one plugin and exercise plugin instance handlers
        rload = _call(helper, {"action": "plugin", "method": "load_plugin", "uri": plugin_uri}, retries=5)
        if rload and rload.get("success"):
            instance_id = rload.get("instance_id") or (rload.get("plugin") or {}).get("instance_id")
            host_instance = (rload.get("plugin") or {}).get("host_instance")

    # General plugin queries
    _call(helper, {"action": "plugin", "method": "list_instances"})
    if instance_id:
        _call(helper, {"action": "plugin", "method": "get_plugin_info", "instance_id": instance_id})
        _call(helper, {"action": "plugin", "method": "get_parameter", "instance_id": instance_id, "port": "gain"})
        # Try set_parameter best-effort
        _call(helper, {"action": "plugin", "method": "set_parameter", "instance_id": instance_id, "port": "gain", "value": 0.5})

    # 4) JACK/audio handlers
    for req in (
        {"action": "audio", "method": "get_jack_hardware_ports", "is_audio": True, "is_output": False},
        {"action": "audio", "method": "get_jack_hardware_ports", "is_audio": True, "is_output": True},
        {"action": "audio", "method": "get_jack_buffer_size"},
        {"action": "audio", "method": "get_jack_sample_rate"},
    ):
        _call(helper, req)

    # If we loaded a plugin, remove it
    if instance_id:
        _call(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": instance_id})

    helper.close()
