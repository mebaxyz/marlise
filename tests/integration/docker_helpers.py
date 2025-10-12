import subprocess
import time
import re


def start_runtime_container(tag: str):
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
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise RuntimeError(f"Failed to discover published ports for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    # Wait for readiness
    ready = False
    deadline = time.time() + 20.0
    while time.time() < deadline:
        state = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_id], stdout=subprocess.PIPE)
        if state.returncode != 0 or state.stdout.decode().strip() != "true":
            logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise RuntimeError(f"Container {container_id} exited prematurely. Logs:\n{logs.stdout.decode(errors='ignore')}")

        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = logs.stdout.decode(errors="ignore")
        if "mod-host ready!" in out or "PROTOCOL:" in out:
            ready = True
            break
        time.sleep(0.25)

    if not ready:
        logs = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise RuntimeError(f"mod-host did not report readiness for container {container_id}. Logs:\n{logs.stdout.decode(errors='ignore')}")

    return container_id, host_port, host_port_fb


def stop_container(container_id: str):
    subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_container_with_modhost(tag: str, stage: str):
    """Run the image once (ephemeral) to execute the installed mod-host binary
    for a quick smoke check. Returns a subprocess.CompletedProcess like
    subprocess.run(...).
    """
    # Run the installed mod-host binary directly as the container entrypoint
    # This avoids running the image entrypoint (which manages jackd) and
    # keeps this check simple: just execute `/opt/marlise/bin/mod-host -V`.
    run_cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "/opt/marlise/bin/mod-host",
        tag,
        "-V",
    ]

    return subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
