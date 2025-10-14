import re
import glob
import os
import pytest
import time

from .zmq_helper import ZMQHelper


HANDLERS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'session_manager', 'handlers')

# Map handler module filename -> action name used in RPC messages
MODULE_ACTION_MAP = {
    'plugin_handlers.py': 'plugin',
    'jack_handlers.py': 'audio',
    'system_handlers.py': 'system',
    'pedalboard_handlers.py': 'pedalboard',
}

# Skip potentially destructive handlers
SKIP_HANDLERS = {
    'shutdown', 'reboot', 'install_update', 'install_package', 'remove_package',
    'delete_file', 'upload_file', 'install_update', 'install_package', 'remove_package',
    'shutdown', 'reboot', 'remove_favorite', 'start_recording', 'stop_recording',
}


def _discover_handlers():
    """Return list of (action, method_name, source_file) discovered from handlers dir."""
    results = []
    pattern = re.compile(r"@zmq_handler\(\s*\"([^\"]+)\"\s*\)")
    files = glob.glob(os.path.join(HANDLERS_DIR, '*.py'))
    for f in files:
        name = os.path.basename(f)
        action = MODULE_ACTION_MAP.get(name, 'session')
        with open(f, 'r') as fh:
            src = fh.read()
        for m in pattern.finditer(src):
            method = m.group(1)
            if method in SKIP_HANDLERS:
                continue
            results.append((action, method, name))
    return results


def _call(helper, req, retries=3, wait=0.25):
    for _ in range(retries):
        try:
            return helper.call(req)
        except Exception:
            time.sleep(wait)
    return None


@pytest.mark.integration
def test_call_all_discovered_handlers(modhost_container):
    container_id, _cmd_port, _fb_port, host_port_zmq, _host_port_pub, _host_port_health = modhost_container

    helper = ZMQHelper(host='127.0.0.1', port=host_port_zmq, timeout_ms=3000)

    handlers = _discover_handlers()
    assert handlers, "No handlers discovered in session_manager/handlers"

    summary = []
    for action, method, src in handlers:
        req = {"action": action, "method": method}
        # Provide some safe defaults for commonly-required params
        if method in ('get_plugin_info', 'get_parameter', 'set_parameter', 'remove_plugin', 'unload_plugin'):
            # instance_id may not exist; call without and let handler respond gracefully
            pass

        try:
            r = _call(helper, req, retries=2)
            ok = isinstance(r, dict)
        except Exception as e:
            r = {'error': str(e)}
            ok = False

        summary.append((action, method, src, ok, r))

    # Log a compact summary for visibility in test output
    good = sum(1 for _a, _m, _s, ok, _r in summary if ok)
    total = len(summary)
    print(f"Called {total} handlers, {good} returned dict-like responses (best-effort)")
    for a, m, s, ok, r in summary:
        status = 'OK' if ok else 'ERR'
        print(f"{status} {a}.{m} (from {s}) -> {r if isinstance(r, dict) else repr(r)[:200]}")

    helper.close()
