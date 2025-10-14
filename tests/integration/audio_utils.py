import subprocess
import time
from typing import Optional, Tuple


def list_jack_ports_container(container_id: str) -> str:
    cmd = ["docker", "exec", container_id, "jack_lsp"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return r.stdout if r.returncode == 0 else ""


def choose_capture_and_playback(container_id: str) -> Optional[Tuple[str, str]]:
    """Return a (capture, playback) port pair from the container's JACK ports, or None if not found.

    This prefers system:capture_* and system:playback_* but will return first found pair.
    """
    out = list_jack_ports_container(container_id)
    captures = [l.strip() for l in out.splitlines() if "system:capture" in l]
    playbacks = [l.strip() for l in out.splitlines() if "system:playback" in l]
    if captures and playbacks:
        return captures[0], playbacks[0]

    # Fallback: look for any port with 'capture' and any with 'playback'
    captures = [l.strip() for l in out.splitlines() if "capture" in l.lower()]
    playbacks = [l.strip() for l in out.splitlines() if "playback" in l.lower()]
    if captures and playbacks:
        return captures[0], playbacks[0]

    return None
