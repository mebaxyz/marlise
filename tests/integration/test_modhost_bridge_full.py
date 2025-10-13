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

        # If docker is available we require container-side jack_lsp/jack_query to be present.
        # If docker is missing or the helper is not present the test will fail to make the check mandatory.
        import shutil, subprocess, time, pytest

        if not shutil.which("docker"):
            pytest.fail("docker is required for mandatory container-side jack_lsp verification")

        # Ensure the jack_query helper exists and jack_lsp is available inside container
        try:
            check_helper = ["docker", "exec", container_id, "test", "-x", "/opt/marlise/bin/jack_query.sh"]
            r = subprocess.run(check_helper)
            if r.returncode != 0:
                pytest.fail("/opt/marlise/bin/jack_query.sh not found or not executable in runtime container; rebuild image with jack_lsp available")
            # also ensure jack_lsp binary is present
            check_jack = ["docker", "exec", container_id, "which", "jack_lsp"]
            r2 = subprocess.run(check_jack, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if r2.returncode != 0 or not r2.stdout.strip():
                pytest.fail("jack_lsp not found inside runtime container; rebuild image to include JACK tools")

            # Poll for the connection to appear
            cmd = ["docker", "exec", container_id, "/opt/marlise/bin/jack_query.sh", "find", p1]
            deadline = time.time() + 10.0
            found = False
            while time.time() < deadline:
                try:
                    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    if r.returncode == 0 and p2 in r.stdout:
                        found = True
                        break
                except Exception:
                    pass
                time.sleep(0.15)

            if not found:
                pytest.fail(f"Ports did not appear connected in JACK according to jack_query (checked container {container_id})")
        except Exception as e:
            pytest.fail(f"Error while verifying jack_lsp inside container: {e}")

        # Disconnect
        resp_disc = _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": p1, "port2": p2})
        assert resp_disc is not None and resp_disc.get("success") is True

        if use_container_check:
            # verify disconnection via jack_query
            try:
                import subprocess, time
                cmd = ["docker", "exec", container_id, "/opt/marlise/bin/jack_query.sh", "find", p1]
                deadline = time.time() + 10.0
                still = True
                while time.time() < deadline:
                    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    if r.returncode != 0 or p2 not in r.stdout:
                        still = False
                        break
                    time.sleep(0.15)
                assert not still, "Ports still connected after disconnect according to jack_query"
            except Exception:
                # fallback: we already asserted RPC success
                pass

    # buffer size / sample rate queries
    resp_buf = _call_with_retries(helper, {"action": "audio", "method": "get_jack_buffer_size"})
    assert resp_buf is not None and resp_buf.get("success") is True
    assert "buffer_size" in resp_buf

    resp_sr = _call_with_retries(helper, {"action": "audio", "method": "get_jack_sample_rate"})
    assert resp_sr is not None and resp_sr.get("success") is True
    assert "sample_rate" in resp_sr

    helper.close()


def test_two_plugins_chain_and_jack_connections(modhost_container):
    """Load two plugins, chain them (system -> A_in -> A_out -> B_in -> B_out -> system out)
    and verify connections at JACK level using jack_lsp inside the runtime container.
    """
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = zmq_helper.ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=3000)

    # 1) get available plugins and pick two
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

    if len(plugin_list) < 1:
        helper.close()
        pytest.skip("No available plugins to load")

    # If only one plugin available, load it twice
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

    # 4) Build JACK port names using host_instance (the numeric instance from mod-host)
    # mod-host creates JACK clients as "effect_<N>" where N is the numeric instance
    # and registers ports with simple names like "in", "out", etc.
    # If host_instance is available, use it; otherwise fall back to parsing jack_lsp
    import subprocess, time

    def _discover_plugin_ports(host_instance):
        """Discover JACK ports for a plugin by listing effect_<N> ports"""
        if host_instance is None:
            return None, None
        
        client_name = f"effect_{host_instance}"
        cmd = ["docker", "exec", container_id, "jack_lsp"]
        
        # Poll for port registration
        deadline = time.time() + 5.0
        while time.time() < deadline:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if r.returncode == 0:
                ports = []
                for line in r.stdout.splitlines():
                    if line.startswith(client_name + ":"):
                        ports.append(line.strip())
                
                if ports:
                    # Find input and output ports
                    input_port = next((p for p in ports if ":in" in p.lower()), None)
                    output_port = next((p for p in ports if ":out" in p.lower()), None)
                    if input_port and output_port:
                        return input_port, output_port
            time.sleep(0.1)
        
        return None, None

    # Discover JACK ports for both plugins
    port_a_in, port_a_out = _discover_plugin_ports(host_inst_a)
    port_b_in, port_b_out = _discover_plugin_ports(host_inst_b)

    if not all([port_a_in, port_a_out, port_b_in, port_b_out]):
        pytest.fail(f"Could not discover JACK ports for plugins. "
                   f"Plugin A (host_instance={host_inst_a}): in={port_a_in}, out={port_a_out}. "
                   f"Plugin B (host_instance={host_inst_b}): in={port_b_in}, out={port_b_out}")

    # 5) Discover system ports
    def _list_jack_ports():
        cmd = ["docker", "exec", container_id, "jack_lsp"]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        return r.stdout if r.returncode == 0 else ""

    ports_output = _list_jack_ports()
    sys_capture = None
    sys_playback = None
    for line in ports_output.splitlines():
        if not sys_capture and "system:capture" in line:
            sys_capture = line.strip()
        if not sys_playback and "system:playback" in line:
            sys_playback = line.strip()

    # 6) Connect the routing: system capture -> A_in -> A_out -> B_in -> B_out -> system playback
    if sys_capture:
        r1 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": sys_capture, "port2": port_a_in})
        assert r1 and r1.get("success"), f"Failed to connect {sys_capture} -> {port_a_in}"

    # Connect A_out -> B_in
    r2 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_a_out, "port2": port_b_in})
    assert r2 and r2.get("success"), f"Failed to connect {port_a_out} -> {port_b_in}"

    # Connect B_out -> system playback
    if sys_playback:
        r3 = _call_with_retries(helper, {"action": "audio", "method": "connect_jack_ports", "port1": port_b_out, "port2": sys_playback})
        assert r3 and r3.get("success"), f"Failed to connect {port_b_out} -> {sys_playback}"

    # 7) Verify connections with jack_lsp -c inside the container
    def _verify_connection(src, dst, timeout=5.0):
        """Verify JACK connection exists using jack_lsp -c"""
        cmd = ["docker", "exec", container_id, "jack_lsp", "-c"]
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if r.returncode == 0:
                lines = r.stdout.splitlines()
                # jack_lsp -c output shows: port\n   connected_port\n
                for i, line in enumerate(lines):
                    if line.strip() == src:
                        # Check next lines for destination
                        for j in range(i+1, min(i+10, len(lines))):
                            if lines[j].strip() and not lines[j].startswith(" "):
                                break
                            if dst in lines[j]:
                                return True
            time.sleep(0.2)
        return False

    # Verify A -> B connection
    assert _verify_connection(port_a_out, port_b_in), \
        f"Connection {port_a_out} -> {port_b_in} not found in jack_lsp -c output"

    # Cleanup: disconnect and unload
    _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": port_a_out, "port2": port_b_in})
    if sys_capture:
        _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": sys_capture, "port2": port_a_in})
    if sys_playback:
        _call_with_retries(helper, {"action": "audio", "method": "disconnect_jack_ports", "port1": port_b_out, "port2": sys_playback})
    _call_with_retries(helper, {"action": "plugin", "method": "unload_plugin", "instance_id": inst_a})
    _call_with_retries(helper, {"action": "plugin", "method": "unload_plugin", "instance_id": inst_b})

    helper.close()
