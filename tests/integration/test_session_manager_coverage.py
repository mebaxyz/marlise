import time
import subprocess
import pytest

from . import zmq_helper


def _call_with_retries(helper, req, retries=3, delay=0.25):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(delay)
    return None


def _discover_plugin_ports(container_id, host_instance, timeout=5.0):
    if host_instance is None:
        return None, None
    client_name = f"effect_{host_instance}"
    cmd = ["docker", "exec", container_id, "jack_lsp"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if r.returncode == 0:
            ports = [l.strip() for l in r.stdout.splitlines() if l.startswith(client_name + ":")]
            if ports:
                input_port = next((p for p in ports if ":in" in p.lower()), None)
                output_port = next((p for p in ports if ":out" in p.lower()), None)
                if input_port and output_port:
                    return input_port, output_port
        time.sleep(0.1)
    return None, None


@pytest.mark.integration
def test_bridge_session_manager_coverage(modhost_container):
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=5000)

    # 1) discover plugins
    resp_plugins = _call_with_retries(helper, {"action": "plugin", "method": "get_available_plugins"}, retries=5)
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
        pytest.skip("No available plugins to load in runtime image")

    uri = plugin_list[0]

    # 2) load plugin A
    resp_a = _call_with_retries(helper, {"action": "plugin", "method": "load_plugin", "uri": uri}, retries=5)
    assert resp_a and resp_a.get("success")
    plugin_a = resp_a.get("plugin") or {}
    inst_a = plugin_a.get("instance_id") or resp_a.get("instance_id")
    host_a = plugin_a.get("host_instance")
    assert inst_a is not None

    # 3) load plugin B
    resp_b = _call_with_retries(helper, {"action": "plugin", "method": "load_plugin", "uri": uri}, retries=5)
    assert resp_b and resp_b.get("success")
    plugin_b = resp_b.get("plugin") or {}
    inst_b = plugin_b.get("instance_id") or resp_b.get("instance_id")
    host_b = plugin_b.get("host_instance")
    assert inst_b is not None

    # 4) Attempt to set a parameter (best-effort, plugin ports vary)
    # Try to set a common port name 'gain' or fallback to listing plugin ports via bridge if available
    param_candidates = ["gain", "volume", "level"]
    set_ok = False
    for pname in param_candidates:
        r = _call_with_retries(helper, {"action": "plugin", "method": "set_parameter", "instance_id": inst_a, "port": pname, "value": 0.5}, retries=2)
        if r and r.get("success"):
            set_ok = True
            break

    # Not a blocker: continue even if parameter set failed

    # 5) (Optional) Try to set a parameter on plugin B (best-effort)
    if inst_b:
        _call_with_retries(helper, {"action": "plugin", "method": "set_parameter", "instance_id": inst_b, "port": param_candidates[0], "value": 0.2}, retries=2)

    # 7) Discover JACK ports for both plugins
    port_a_in, port_a_out = _discover_plugin_ports(container_id, host_a)
    port_b_in, port_b_out = _discover_plugin_ports(container_id, host_b)
    assert port_a_in and port_a_out and port_b_in and port_b_out

    # 6) Connect system capture -> A_in
    ports_output = subprocess.run(["docker", "exec", container_id, "jack_lsp"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    sys_capture = next((l.strip() for l in ports_output.stdout.splitlines() if "system:capture" in l), None)
    sys_playback = next((l.strip() for l in ports_output.stdout.splitlines() if "system:playback" in l), None)
    if sys_capture and sys_playback:
        r1 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": sys_capture, "port2": port_a_in}, retries=3)
        assert r1 and r1.get("success")
        # verify sys_capture connected to port_a_in
        check = subprocess.run(["docker", "exec", container_id, "jack_lsp", "-c", port_a_in], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        assert sys_capture in check.stdout

        # Chain A_out -> B_in
        r2 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_a_out, "port2": port_b_in}, retries=3)
        assert r2 and r2.get("success")
        # verify a_out connected to b_in
        check2 = subprocess.run(["docker", "exec", container_id, "jack_lsp", "-c", port_b_in], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        assert port_a_out in check2.stdout

        # B_out -> system playback
        r3 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_b_out, "port2": sys_playback}, retries=3)
        assert r3 and r3.get("success")
        # verify b_out connected to system playback
        check3 = subprocess.run(["docker", "exec", container_id, "jack_lsp", "-c", sys_playback], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        assert port_b_out in check3.stdout

    # Verify via jack_lsp that ports exist (connectivity is best-effort here)
    jl = subprocess.run(["docker", "exec", container_id, "jack_lsp"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    assert port_a_in in jl.stdout and port_b_out in jl.stdout

    # 7) Remove plugin instances
    _call_with_retries(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": inst_a}, retries=2)
    _call_with_retries(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": inst_b}, retries=2)

    helper.close()
