import subprocess
import time
import re


def start_runtime_container(tag: str):
    use_host_network = False
    try:
        import os
        env_val = os.environ.get("MODHOST_TEST_USE_HOST_NETWORK", "").strip().lower()
        use_host_network = env_val in ("1", "true", "yes")
    except Exception:
        use_host_network = False

    if use_host_network:
        # Use host networking for easier access to bridge and mod-host bound to localhost
        run_cmd = [
            "docker",
            "run",
            "-d",
            "--network",
            "host",
            "-e",
            "JACK_DUMMY=1",
            "-e",
            "MODHOST_BRIDGE_REP=tcp://0.0.0.0:6000",
            "-e",
            "MODHOST_BRIDGE_PUB=tcp://0.0.0.0:6001",
            "-e",
            "MODHOST_BRIDGE_HEALTH=tcp://0.0.0.0:6002",
            tag,
        ]
        # Corresponding host ports when using host network
        host_port = 5555
        host_port_fb = 5556
        host_port_zmq = 6000
        host_port_pub = 6001
        host_port_health = 6002
    else:
        run_cmd = [
            "docker",
            "run",
            "-d",
            "--expose",
            "5555",
            "--expose",
            "5556",
            "--expose",
            "6000",
            "--expose",
            "6001",
            "--expose",
            "6002",
            "-P",
            "-e",
            "JACK_DUMMY=1",
            "-e",
            "MODHOST_BRIDGE_REP=tcp://0.0.0.0:6000",
            "-e",
            "MODHOST_BRIDGE_PUB=tcp://0.0.0.0:6001",
            "-e",
            "MODHOST_BRIDGE_HEALTH=tcp://0.0.0.0:6002",
            tag,
        ]
    container_id = subprocess.check_output(run_cmd).decode().strip()
    host_port = None
    host_port_fb = None
    host_port_zmq = None
    host_port_pub = None
    host_port_health = None
    if use_host_network:
        # When using host networking the services are reachable on the host's loopback
        host_port = 5555
        host_port_fb = 5556
        host_port_zmq = 6000
        host_port_pub = 6001
        host_port_health = 6002
    else:
        for _ in range(40):
            proc_cmd = subprocess.run(["docker", "port", container_id, "5555"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_fb = subprocess.run(["docker", "port", container_id, "5556"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_zmq = subprocess.run(["docker", "port", container_id, "6000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_pub = subprocess.run(["docker", "port", container_id, "6001"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_health = subprocess.run(["docker", "port", container_id, "6002"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if (
                proc_cmd.returncode == 0
                and proc_cmd.stdout.strip()
                and proc_fb.returncode == 0
                and proc_fb.stdout.strip()
                and proc_zmq.returncode == 0
                and proc_zmq.stdout.strip()
                and proc_pub.returncode == 0
                and proc_pub.stdout.strip()
                and proc_health.returncode == 0
                and proc_health.stdout.strip()
            ):
                mapping = proc_cmd.stdout.decode().strip()
                mapping_fb = proc_fb.stdout.decode().strip()
                mapping_zmq = proc_zmq.stdout.decode().strip()
                mapping_pub = proc_pub.stdout.decode().strip()
                mapping_health = proc_health.stdout.decode().strip()
                m = re.search(r":(\d+)$", mapping)
                mfb = re.search(r":(\d+)$", mapping_fb)
                mz = re.search(r":(\d+)$", mapping_zmq)
                mp = re.search(r":(\d+)$", mapping_pub)
                mh = re.search(r":(\d+)$", mapping_health)
                if m and mfb and mz:
                    host_port = int(m.group(1))
                    host_port_fb = int(mfb.group(1))
                    host_port_zmq = int(mz.group(1))
                    host_port_pub = int(mp.group(1)) if mp else None
                    host_port_health = int(mh.group(1)) if mh else None
                    break
            time.sleep(0.25)

        if host_port is None or host_port_fb is None or host_port_zmq is None or host_port_pub is None or host_port_health is None:
            logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise RuntimeError(f"Failed to discover published ports for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")
    # Wait for readiness: mod-host and modhost-bridge may take some time to
    # initialize. Look for mod-host readiness or ZeroMQ/bridge startup logs.
    ready = False
    deadline = time.time() + 40.0
    while time.time() < deadline:
        state = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_id], stdout=subprocess.PIPE)
        if state.returncode != 0 or state.stdout.decode().strip() != "true":
            logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise RuntimeError(f"Container {container_id} exited prematurely. Logs:\n{logs.stdout.decode(errors='ignore')}")

        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = logs.stdout.decode(errors="ignore")
        # Bridge prints ZeroMQ endpoints at startup; also accept "All services"
        if (
            "mod-host ready!" in out
            or "PROTOCOL:" in out
            or "ZeroMQ:" in out
            or "All services started successfully" in out
            or "modhost-bridge PID" in out
        ):
            ready = True
            break
        time.sleep(0.25)

    if not ready:
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise RuntimeError(f"mod-host did not report readiness for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    # Return (container_id, cmd_port, fb_port, zmq_cmd_port, zmq_pub_port, zmq_health_port)
    return container_id, host_port, host_port_fb, host_port_zmq, host_port_pub, host_port_health


def stop_container(container_id: str):
    subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_container_with_modhost(tag: str, stage: str):
    """Run the image once (ephemeral) to execute the installed mod-host binary
    for a quick smoke check. Returns a subprocess.CompletedProcess like
    subprocess.run(...).
    """
    # Start the container with the normal entrypoint so the bridge and jackd
    # are started too. Then exec the mod-host binary inside the running
    # container to run `mod-host -V` for a simple smoke check.
    run_cmd = [
        "docker",
        "run",
        "-d",
        "--expose",
        "5555",
        "--expose",
        "5556",
        "--expose",
        "6000",
        "-e",
        "JACK_DUMMY=1",
        "-e",
        "MODHOST_BRIDGE_REP=tcp://0.0.0.0:6000",
        "-e",
        "MODHOST_BRIDGE_PUB=tcp://0.0.0.0:6001",
        "-e",
        "MODHOST_BRIDGE_HEALTH=tcp://0.0.0.0:6002",
        tag,
    ]
    container_id = subprocess.check_output(run_cmd).decode().strip()

    try:
        # Wait briefly for container to initialize
        deadline = time.time() + 10.0
        ready = False
        while time.time() < deadline:
            logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = logs.stdout.decode(errors="ignore")
            if "mod-host ready!" in out or "PROTOCOL:" in out or "modhost-bridge" in out:
                ready = True
                break
            time.sleep(0.25)

        # Exec the binary inside the container to check version
        exec_cmd = ["docker", "exec", "--tty", container_id, "/opt/marlise/bin/mod-host", "-V"]
        res = subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        return res
    finally:
        # Ensure container removed
        subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
