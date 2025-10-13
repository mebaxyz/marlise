import pytest
import time

from .zmq_helper import ZMQHelper


def _call(helper, req, retries=3, wait=0.5):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(wait)
    return None


@pytest.mark.integration
def test_plugin_metadata_basic():
    helper = ZMQHelper()
    resp = _call(helper, {"action": "plugin", "method": "get_available_plugins"}, retries=5)
    assert resp and resp.get("success")
    plugins = resp.get("plugins", {})
    if not plugins:
        pytest.skip("No LV2 plugins available in test environment")
    if isinstance(plugins, dict):
        plugin_list = list(plugins.values())
    else:
        plugin_list = plugins
    if not plugin_list:
        pytest.skip("No LV2 plugins available in test environment")
    plugin_uri = plugin_list[0].get("uri")

    # load plugin
    resp_load = _call(helper, {"action": "plugin", "method": "load_plugin", "uri": plugin_uri}, retries=5)
    assert resp_load and resp_load.get("success")
    inst = resp_load.get("instance_id")

    # get_plugin_info
    info = _call(helper, {"action": "plugin", "method": "get_plugin_info", "instance_id": inst}, retries=3)
    assert info is not None

    # get_plugin_essentials / GUI (best-effort)
    ess = _call(helper, {"action": "plugin", "method": "get_plugin_essentials", "instance_id": inst}, retries=2)
    gui = _call(helper, {"action": "plugin", "method": "get_plugin_gui", "instance_id": inst}, retries=2)
    assert ess is not None
    # gui may be empty for some plugins; we only assert that we got a response
    assert gui is not None

    # cleanup
    _call(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": inst})
    helper.close()
