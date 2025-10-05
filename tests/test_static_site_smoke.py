import os
import subprocess
import time

import pytest


def is_command_available(cmd):
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


@pytest.mark.skipif(not is_command_available("docker"), reason="docker not available")
def test_static_site_serves_index(tmp_path):
    """Smoke test: bring up the static-site service and check it serves an index.html

    This test calls the development compose file. It's intentionally conservative and
    cleans up after itself.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    compose = os.path.join(repo_root, "docker", "docker-compose.dev.yml")

    # Start service
    up = subprocess.run(["docker", "compose", "-f", compose, "up", "-d", "static-site"], cwd=repo_root)
    assert up.returncode == 0

    try:
        # wait for nginx to be ready (try localhost:80)
        deadline = time.time() + 30
        ok = False
        while time.time() < deadline:
            proc = subprocess.run(["curl", "-sS", "-I", "http://127.0.0.1:80"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            out = proc.stdout.decode(errors="ignore")
            if "200 OK" in out or "301" in out or "302" in out:
                ok = True
                break
            time.sleep(0.5)

        assert ok, "static-site did not respond with HTTP 200/3xx within 30s"

    finally:
        # Tear down the service
        subprocess.run(["docker", "compose", "-f", compose, "down"], cwd=repo_root)
