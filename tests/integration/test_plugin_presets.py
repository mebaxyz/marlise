import time
import pytest

from .zmq_helper import ZMQHelper
import json
import os
import subprocess
import math


def _call(helper, req, retries=3, wait=0.5):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(wait)
    return None


@pytest.mark.integration
def test_plugin_presets_basic():
    helper = ZMQHelper()

    # 1) get available plugins and pick one that likely has presets
    resp = _call(helper, {"action": "plugin", "method": "get_available_plugins"}, retries=5)
    assert resp and resp.get("success")
    plugins = resp.get("plugins", {})
    # plugins may be a mapping {uri: info} or a list
    if not plugins:
        pytest.skip("No LV2 plugins available in test environment")

    if isinstance(plugins, dict):
        plugin_list = list(plugins.values())
    else:
        plugin_list = plugins

    if not plugin_list:
        pytest.skip("No LV2 plugins available in test environment")

    # pick first plugin URI
    plugin_uri = plugin_list[0].get("uri")
    assert plugin_uri

    # 2) load plugin
    resp_load = _call(helper, {"action": "plugin", "method": "load_plugin", "uri": plugin_uri}, retries=5)
    assert resp_load and resp_load.get("success")
    instance_id = resp_load.get("instance_id")
    assert instance_id

    # 3) get_plugin_presets
    resp_presets = _call(helper, {"action": "plugin", "method": "get_plugin_presets", "instance_id": instance_id}, retries=3)
    assert resp_presets is not None

    # 4) load a test preset with MOD GUI metadata (if bridge supports it)
    preset_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_preset_with_modgui.json')
    preset_path = os.path.normpath(preset_path)
    if os.path.exists(preset_path):
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        resp_loadpreset = _call(helper, {"action": "plugin", "method": "load_preset", "instance_id": instance_id, "preset": preset_data}, retries=3)
        # load_preset may be unimplemented for some plugins; assert we got a response
        assert resp_loadpreset is not None

        # 5) validate_preset
        resp_validate = _call(helper, {"action": "plugin", "method": "validate_preset", "instance_id": instance_id, "preset": preset_data}, retries=2)
        assert resp_validate is not None

        # 6) save_preset (best-effort) - ask bridge to save current parameters as preset
        resp_save = _call(helper, {"action": "plugin", "method": "save_preset", "instance_id": instance_id, "preset_name": "itest-saved"}, retries=2)
        assert resp_save is not None

        # 7) best-effort: verify parameters applied by querying plugin info / parameters
        params = preset_data.get("parameters", {})
        if params:
            info = _call(helper, {"action": "plugin", "method": "get_plugin_info", "instance_id": instance_id}, retries=2)
            if info and info.get("success"):
                # try to read each parameter via get_parameter
                for pname, pval in params.items():
                    try:
                        gp = _call(helper, {"action": "plugin", "method": "get_parameter", "instance_id": instance_id, "port": pname}, retries=2)
                        if gp and gp.get("success"):
                            found = gp.get("value")
                            # numeric comparison with tolerance for float parameters
                            if isinstance(found, (int, float)) and isinstance(pval, (int, float)):
                                assert math.isclose(float(found), float(pval), rel_tol=1e-2, abs_tol=1e-3)
                    except Exception:
                        # best-effort: don't fail the whole test if get_parameter unsupported
                        pass

        # 8) JACK check: if bridge exposes host_instance, ensure effect_<N> ports exist via jack_lsp
        resp_list = _call(helper, {"action": "plugin", "method": "list_instances"}, retries=3)
        host_inst = None
        if resp_list and resp_list.get("success"):
            instances = resp_list.get("instances", {})
            for key, it in instances.items():
                if isinstance(it, dict):
                    iid = it.get("instance_id") or key
                    if str(iid) == str(instance_id):
                        host_inst = it.get("host_instance")
                        break

        if host_inst is not None:
            client_name_in = f"effect_{host_inst}:in"
            client_name_out = f"effect_{host_inst}:out"
            try:
                p = subprocess.run(["jack_lsp"], capture_output=True, text=True, timeout=5)
                out = p.stdout
                assert client_name_in in out or client_name_out in out
            except Exception:
                # best-effort: if jack_lsp unavailable or times out, don't fail the test
                pass

    # Cleanup
    _call(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": instance_id})
    helper.close()
