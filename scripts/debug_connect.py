#!/usr/bin/env python3
"""Debug helper: query JACK hardware ports and attempt connect via ZeroMQ bridge.

Usage: .venv-integration/bin/python scripts/debug_connect.py

This script assumes a running runtime container named `test_br` with the bridge
exposed on tcp://127.0.0.1:6000 (default). Adjust the host/port below if needed.
"""
import subprocess
import time
import sys
import os

# Ensure repository root is on sys.path so we can import tests helpers
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from tests.integration.zmq_helper import ZMQHelper


def main():
    host = "127.0.0.1"
    port = 6000
    helper = ZMQHelper(host=host, port=port, timeout_ms=3000)

    print("Calling get_jack_hardware_ports...")
    try:
        resp = helper.call({"action": "audio", "method": "get_jack_hardware_ports", "is_audio": True, "is_output": False})
    except Exception as e:
        print("ZeroMQ call failed:", e)
        return

    print("Response:", resp)
    ports = resp.get("ports") or []
    print(f"Found {len(ports)} ports")
    if len(ports) < 2:
        print("Not enough ports to attempt connect. Exiting.")
        return

    p1 = ports[0]
    p2 = ports[1]
    print(f"Attempting to connect {p1} -> {p2}")
    try:
        cresp = helper.call({"action": "audio", "method": "connect_jack_ports", "port1": p1, "port2": p2})
    except Exception as e:
        print("connect_jack_ports call failed:", e)
        return

    print("connect_jack_ports response:", cresp)

    # Inspect jack_lsp -c inside container `test_br`
    try:
        print("Inspecting jack_lsp -c for target port on container 'test_br'...")
        chk = subprocess.run(["docker", "exec", "test_br", "jack_lsp", "-c", p2], capture_output=True, text=True, timeout=5)
        print("jack_lsp -c output:")
        print(chk.stdout)
    except Exception as e:
        print("Error running docker exec jack_lsp:", e)

    helper.close()


if __name__ == "__main__":
    main()
