import time
import pytest
import subprocess

from .zmq_helper import ZMQHelper
from .audio_utils import choose_capture_and_playback


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


def _discover_plugin_ports(container_id: str, host_instance):
    if host_instance is None:
        return None, None

    client_name = f"effect_{host_instance}"
    cmd = ["docker", "exec", container_id, "jack_lsp"]
    deadline = time.time() + 5.0
    while time.time() < deadline:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if r.returncode == 0:
            ports = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith(client_name + ":")]
            if ports:
                input_port = next((p for p in ports if ":in" in p.lower()), None)
                output_port = next((p for p in ports if ":out" in p.lower()), None)
                if input_port and output_port:
                    return input_port, output_port
        time.sleep(0.1)
    return None, None


@pytest.mark.integration
def test_session_manager_end_to_end(modhost_container):
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=5000)

    # 1) get available plugins
    resp_plugins = _call_with_retries(helper, {"action": "plugin", "method": "get_available_plugins"})
    assert resp_plugins and resp_plugins.get("success")
    plugins_payload = resp_plugins.get("plugins")
    plugin_list = []
    if isinstance(plugins_payload, dict):
        plugin_list = list(plugins_payload.keys())
    elif isinstance(plugins_payload, list):
        for p in plugins_payload:
            if isinstance(p, dict) and p.get("uri"):
                plugin_list.append(p.get("uri"))

    if not plugin_list:
        helper.close()
        pytest.skip("No available plugins to load")

    uri_a = plugin_list[0]
    uri_b = plugin_list[1] if len(plugin_list) > 1 else plugin_list[0]

    # 2) load plugin A
    resp_load_a = _call_with_retries(helper, {"action": "plugin", "method": "load_plugin", "uri": uri_a})
    assert resp_load_a and resp_load_a.get("success")
    plugin_a = resp_load_a.get("plugin") or {}
    inst_a = plugin_a.get("instance_id") or resp_load_a.get("instance_id")
    host_inst_a = plugin_a.get("host_instance")
    assert inst_a, f"failed to load plugin A: {resp_load_a!r}"

    # 3) load plugin B
    resp_load_b = _call_with_retries(helper, {"action": "plugin", "method": "load_plugin", "uri": uri_b})
    assert resp_load_b and resp_load_b.get("success")
    plugin_b = resp_load_b.get("plugin") or {}
    inst_b = plugin_b.get("instance_id") or resp_load_b.get("instance_id")
    host_inst_b = plugin_b.get("host_instance")
    assert inst_b, f"failed to load plugin B: {resp_load_b!r}"

    # 4) discover JACK ports for plugins
    port_a_in, port_a_out = _discover_plugin_ports(container_id, host_inst_a)
    port_b_in, port_b_out = _discover_plugin_ports(container_id, host_inst_b)

    if not all([port_a_in, port_a_out, port_b_in, port_b_out]):
        # Best-effort: try to fail with useful debug info
        helper.close()
        pytest.fail(f"Could not discover plugin JACK ports. A: {host_inst_a} -> {port_a_in}/{port_a_out}; B: {host_inst_b} -> {port_b_in}/{port_b_out}")

    # 5) discover system capture/playback
    pair = choose_capture_and_playback(container_id)
    sys_capture, sys_playback = (pair if pair else (None, None))

    # 6) Connect routing: sys_capture -> A_in ; A_out -> B_in ; B_out -> sys_playback
    if sys_capture:
        r1 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": sys_capture, "port2": port_a_in})
        assert r1 and r1.get("success"), f"Failed to connect {sys_capture} -> {port_a_in}: {r1}"

    r2 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_a_out, "port2": port_b_in})
    assert r2 and r2.get("success"), f"Failed to connect {port_a_out} -> {port_b_in}: {r2}"

    if sys_playback:
        r3 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_b_out, "port2": sys_playback})
        assert r3 and r3.get("success"), f"Failed to connect {port_b_out} -> {sys_playback}: {r3}"

    # 7) verify connections using jack_lsp -c
    def _verify_connection(src, dst, timeout=5.0):
        cmd = ["docker", "exec", container_id, "jack_lsp", "-c"]
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if r.returncode == 0:
                lines = r.stdout.splitlines()
                for i, line in enumerate(lines):
                    if line.strip() == src:
                        for j in range(i+1, min(i+10, len(lines))):
                            if lines[j].strip() and not lines[j].startswith(" "):
                                break
                            if dst in lines[j]:
                                return True
            time.sleep(0.2)
        return False

    assert _verify_connection(port_a_out, port_b_in), f"Connection {port_a_out} -> {port_b_in} not found"

    # 8) cleanup
    _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": port_a_out, "port2": port_b_in})
    if sys_capture:
        _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": sys_capture, "port2": port_a_in})
    if sys_playback:
        _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": port_b_out, "port2": sys_playback})

    # unload plugins
    _call_with_retries(helper, {"action": "plugin", "method": "unload_plugin", "instance_id": inst_a})
    _call_with_retries(helper, {"action": "plugin", "method": "unload_plugin", "instance_id": inst_b})

    helper.close()
