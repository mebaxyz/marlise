import time
import pytest

from .zmq_helper import ZMQHelper


def _call_with_retries(helper, req, timeout_s=10.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            return helper.call(req)
        except Exception:
            time.sleep(0.2)
    return None


@pytest.mark.integration
def test_snapshot_roundtrip(modhost_container):
    """Strict snapshot test: save snapshot, remove loaded instances, load snapshot, assert instances restored."""
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = ZMQHelper(host="127.0.0.1", port=host_port_zmq, timeout_ms=5000)

    # 1) ensure there's at least one plugin loaded for meaningful snapshot
    resp_list = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
    assert resp_list is not None and resp_list.get("success") is True
    instances_before = resp_list.get("instances") or []
    count_before = len(instances_before) if isinstance(instances_before, list) else len(list(instances_before.keys()))

    # If no instances, load one plugin to have content to snapshot
    if count_before == 0:
        resp_plugins = _call_with_retries(helper, {"action": "plugin", "method": "get_available_plugins"})
        assert resp_plugins and resp_plugins.get("success")
        plugins_payload = resp_plugins.get("plugins") or {}
        plugin_uri = None
        if isinstance(plugins_payload, dict):
            for k in plugins_payload.keys():
                plugin_uri = k
                break
        elif isinstance(plugins_payload, list) and plugins_payload:
            plugin_uri = plugins_payload[0].get("uri") if isinstance(plugins_payload[0], dict) else None

        if not plugin_uri:
            helper.close()
            pytest.skip("No LV2 plugins available to create a snapshot")

        resp_load = _call_with_retries(helper, {"action": "plugin", "method": "load_plugin", "uri": plugin_uri})
        assert resp_load and resp_load.get("success")

        resp_list = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
        instances_before = resp_list.get("instances") or []
        count_before = len(instances_before) if isinstance(instances_before, list) else len(list(instances_before.keys()))

    assert count_before > 0, "No plugin instances available to snapshot"

    # 2) Save snapshot using common RPC names; require success for at least one
    snap_name = f"itest-snap-{int(time.time())}"
    save_variants = [
        {"action": "session", "method": "save_snapshot", "name": snap_name},
        {"action": "session", "method": "save_session", "name": snap_name},
        {"action": "system", "method": "save_snapshot", "name": snap_name},
    ]
    saved = False
    for sreq in save_variants:
        r = _call_with_retries(helper, sreq)
        if r and r.get("success"):
            saved = True
            break

    assert saved, f"Failed to save snapshot with any known RPC variant ({snap_name})"

    # 3) Remove all plugin instances (best-effort)
    resp_list2 = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
    instances_now = resp_list2.get("instances") or {}
    # Normalize to list of instance ids
    ids = []
    if isinstance(instances_now, dict):
        for k, v in instances_now.items():
            if isinstance(v, dict) and v.get("instance_id"):
                ids.append(v.get("instance_id"))
            else:
                ids.append(k)
    elif isinstance(instances_now, list):
        for v in instances_now:
            if isinstance(v, dict) and v.get("instance_id"):
                ids.append(v.get("instance_id"))

    for iid in ids:
        _call_with_retries(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": iid})

    # Ensure there are zero instances now
    resp_after_remove = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
    instances_removed = resp_after_remove.get("instances") or {}
    count_removed = len(instances_removed) if isinstance(instances_removed, list) else len(list(instances_removed.keys()))
    assert count_removed == 0, f"Failed to remove all plugin instances; remaining: {count_removed}"

    # 4) Load snapshot back
    load_variants = [
        {"action": "session", "method": "load_snapshot", "name": snap_name},
        {"action": "session", "method": "load_session", "name": snap_name},
        {"action": "system", "method": "load_snapshot", "name": snap_name},
    ]
    loaded = False
    for lreq in load_variants:
        r = _call_with_retries(helper, lreq)
        if r and r.get("success"):
            loaded = True
            break

    assert loaded, f"Failed to load snapshot {snap_name} with any known RPC variant"

    # 5) Verify instances restored (count should match or be >= 1)
    resp_final = _call_with_retries(helper, {"action": "plugin", "method": "list_instances"})
    instances_final = resp_final.get("instances") or {}
    count_final = len(instances_final) if isinstance(instances_final, list) else len(list(instances_final.keys()))
    assert count_final >= 1, "No plugin instances restored after loading snapshot"

    # Cleanup: remove restored instances
    ids_final = []
    if isinstance(instances_final, dict):
        for k, v in instances_final.items():
            if isinstance(v, dict) and v.get("instance_id"):
                ids_final.append(v.get("instance_id"))
            else:
                ids_final.append(k)
    elif isinstance(instances_final, list):
        for v in instances_final:
            if isinstance(v, dict) and v.get("instance_id"):
                ids_final.append(v.get("instance_id"))

    for iid in ids_final:
        _call_with_retries(helper, {"action": "plugin", "method": "remove_plugin", "instance_id": iid})

    helper.close()
