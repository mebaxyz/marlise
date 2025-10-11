# Audio Engine Docker Image

This container image bundles the `mod-host` audio host and the `modhost-bridge` into a self-contained Docker image. It includes an optional dummy JACK server for smoke testing.

## Build

```bash
# From the repository root
docker build -t marlise-audio:local -f deployment/audio-engine/Dockerfile .
```

## Run (Dummy JACK)

Use the `JACK_DUMMY` environment variable to start JACK in dummy mode inside the container. You can disable `pw-jack` by setting `USE_PWJACK=0`.

```bash
docker run --rm \
  -e JACK_DUMMY=1 \
  -e USE_PWJACK=0 \
  -p 5555:5555 -p 5556:5556 \
  marlise-audio:local
```

- `5555` is the command socket for `mod-host`.
- `5556` is the feedback socket.

## Smoke Test (Ping)

You can test the `ping` command (health check) by sending a null-terminated `ping` string and reading the response from port `5555`:

```bash
python3 - <<EOF
import socket
# Connect to command and feedback ports
cmd = socket.socket()
fb = socket.socket()
cmd.connect(('127.0.0.1', 5555))
fb.connect(('127.0.0.1', 5556))
cmd.sendall(b'ping\x00')
print(cmd.recv(1024))  # Expected: b'resp 0\\x00'
cmd.close()
fb.close()
EOF
```

If you see `b'resp 0\x00'`, the `mod-host` is responding to health checks correctly.
