import os
import subprocess
import tempfile
import time
import socket
import re
import pytest


def _run_container_with_modhost(tag: str, stage: str):
    """Run the builder image in a short-lived container to execute the
    built mod-host binary for a smoke check. The builder stage contains
    the mod-host executable at `/src/mod-host/mod-host` (copied into the
    runtime image at `/opt/marlise/bin/mod-host` by the final Dockerfile
    step). For the smoke test we run the binary directly in the builder
    image's container filesystem, not the final runtime image.
    """
    # Create a container and run the binary directly. Use the appropriate
    # binary path depending on which image stage was built.
    if stage == "builder":
        run_cmd = [
            "docker",
            "run",
            "--rm",
            tag,
            "/bin/bash",
            "-lc",
            "if [ -x /src/mod-host/mod-host ]; then /src/mod-host/mod-host -V; else echo 'mod-host binary not found' && exit 2; fi",
        ]
    else:
        # For the runtime image ensure a JACK dummy server is started inside
        # the container before invoking the installed binary to avoid JACK
        # client creation failures.
        run_cmd = [
            "docker",
            "run",
            "--rm",
            tag,
            "/bin/bash",
            "-lc",
            "mkdir -p /opt/logs && jackd -d dummy -r 48000 -p 256 -P 2 -C 2 >/opt/logs/jack.log 2>&1 & sleep 0.5; if [ -x /opt/marlise/bin/mod-host ]; then /opt/marlise/bin/mod-host -V; else echo 'mod-host binary not found' && exit 2; fi",
        ]
    return subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)


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
    if stage == "builder":
        run_cmd = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--expose",
            "5555",
            "-P",
            tag,
            "/src/mod-host/mod-host",
            "-n",
            "-p",
            "5555",
            "-f",
            "5556",
        ]
    else:
        # Start a dummy JACK server inside the container then run mod-host so
        # it can create JACK clients. We run jackd in the background and then
        # start mod-host with the expected arguments.
        run_cmd = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--expose",
            "5555",
            "-P",
            tag,
            "/bin/bash",
            "-lc",
            "mkdir -p /opt/logs && jackd -d dummy -r 48000 -p 256 -P 2 -C 2 >/opt/logs/jack.log 2>&1 & sleep 0.5; /opt/marlise/bin/mod-host -n -p 5555 -f 5556",
        ]
    container_id = subprocess.check_output(run_cmd).decode().strip()

    # Query the published port mapping for container:5555
    host_port = None
    for _ in range(40):
        proc = subprocess.run(["docker", "port", container_id, "5555"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0 and proc.stdout.strip():
            mapping = proc.stdout.decode().strip()
            m = re.search(r":(\d+)$", mapping)
            if m:
                host_port = int(m.group(1))
                break
        time.sleep(0.25)

    if host_port is None:
        # Provide container logs to help debugging
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raise RuntimeError(f"Failed to discover published port for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    return container_id, host_port


def test_modhost_ping_socket(modhost_image_tag):
    tag, stage = modhost_image_tag
    container_id = None
    try:
        container_id, host_port = _start_modhost_container(tag, stage)

        # Try to connect and send a ping command until we get a response
        received = None
        deadline = time.time() + 20.0
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", host_port), timeout=2) as s:
                    s.settimeout(2.0)
                    s.sendall(b"ping\n")
                    data = s.recv(4096)
                    received = data.decode(errors="ignore")
                    break
            except (ConnectionRefusedError, TimeoutError, OSError):
                time.sleep(0.25)

        assert received is not None, f"No response from mod-host command port after retries (container={container_id})"
        assert "resp" in received.lower(), f"Unexpected response from mod-host: {received}"

    finally:
        if container_id:
            subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
