import os
import subprocess
import tempfile
import time
import socket
import re
import pytest

from . import docker_helpers


def _run_container_with_modhost(tag: str, stage: str):
    # Delegate to centralized helper for a short-lived smoke run
    return docker_helpers.run_container_with_modhost(tag, stage)


def test_modhost_smoke(modhost_image_tag):
    tag, stage = modhost_image_tag
    res = _run_container_with_modhost(tag, stage)
    out = res.stdout.decode(errors="ignore")
    assert res.returncode == 0, f"mod-host smoke command failed: exit={res.returncode}\n{out}"
    assert "mod-host" in out.lower() or "version" in out.lower()


def _start_modhost_container(tag: str, stage: str):
    """Start a detached container running mod-host (builder image) and
    return (container_id, host_port) where host_port is the randomly
    assigned host port mapping of container port 5555.
    """
    # Run detached, expose the container port and publish randomly (-P).
    # Use the appropriate binary path for builder vs runtime images. For the
    # runtime image we override the entrypoint to execute the installed
    # `/opt/marlise/bin/mod-host` binary directly so the test does not depend
    # on the image entrypoint behavior.
    # Runtime-only: publish both command+feedback via random host ports and enable JACK_DUMMY
    run_cmd = [
        "docker",
        "run",
        "-d",
        "--expose",
        "5555",
        "--expose",
        "5556",
        "-P",
        "-e",
        "JACK_DUMMY=1",
        tag,
    ]
    container_id = subprocess.check_output(run_cmd).decode().strip()

    # Query the published port mapping for container:5555 and 5556
    host_port = None
    host_port_fb = None
    for _ in range(40):
        proc_cmd = subprocess.run(["docker", "port", container_id, "5555"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_fb = subprocess.run(["docker", "port", container_id, "5556"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc_cmd.returncode == 0 and proc_cmd.stdout.strip() and proc_fb.returncode == 0 and proc_fb.stdout.strip():
            mapping = proc_cmd.stdout.decode().strip()
            mapping_fb = proc_fb.stdout.decode().strip()
            m = re.search(r":(\d+)$", mapping)
            mfb = re.search(r":(\d+)$", mapping_fb)
            if m and mfb:
                host_port = int(m.group(1))
                host_port_fb = int(mfb.group(1))
                break
        time.sleep(0.25)

    if host_port is None or host_port_fb is None:
        # Provide container logs to help debugging
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raise RuntimeError(f"Failed to discover published ports for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    # Wait for mod-host to report readiness in the container logs. This avoids
    # flaky timing where the container is up but mod-host hasn't created the
    # server socket yet. Poll logs for an indicative string for up to 20s.
    ready = False
    deadline = time.time() + 20.0
    while time.time() < deadline:
        # Check if the container is still running
        state = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_id], stdout=subprocess.PIPE)
        if state.returncode != 0 or state.stdout.decode().strip() != "true":
            # container exited; include logs in error
            logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            raise RuntimeError(f"Container {container_id} exited prematurely. Logs:\n{logs.stdout.decode(errors='ignore')}")

        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = logs.stdout.decode(errors="ignore")
        if "mod-host ready!" in out or "PROTOCOL:" in out:
            ready = True
            break
        time.sleep(0.25)

    if not ready:
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raise RuntimeError(f"mod-host did not report readiness for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    return container_id, host_port, host_port_fb


def test_modhost_ping_socket(modhost_container):
    container_id, host_port, host_port_fb = modhost_container

    # Try to connect command and feedback sockets, then send a ping and read
    # response. Both sockets must be connected before sending commands.
    received = None
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", host_port), timeout=3) as cmd_sock:
                with socket.create_connection(("127.0.0.1", host_port_fb), timeout=3) as fb_sock:
                    cmd_sock.settimeout(3.0)
                    fb_sock.settimeout(1.0)

                    # send null-terminated ping per README smoke test
                    cmd_sock.sendall(b"ping\x00")

                    # Read from command socket until null terminator or timeout
                    chunks = []
                    read_deadline = time.time() + 3.0
                    while time.time() < read_deadline:
                        try:
                            chunk = cmd_sock.recv(4096)
                        except socket.timeout:
                            break
                        if not chunk:
                            break
                        chunks.append(chunk)
                        if b"\x00" in chunk:
                            break

                    if chunks:
                        received = b"".join(chunks)
                        break
        except (ConnectionRefusedError, TimeoutError, OSError):
            time.sleep(0.25)
    assert received is not None, f"No response from mod-host command port after retries (container={container_id})"
    # Expect a null-terminated resp message, e.g. b'resp 0\x00'
    assert b"resp" in received.lower(), f"Unexpected response from mod-host: {received!r}"
