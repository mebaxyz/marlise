Scripts to start and stop the audio host components (copied from `mado-audio-host/scripts`).

Files:

- `start-service.sh` — starts `mod-host` and `modhost-bridge`, writes PID files to `run/` and logs to `logs/`.
- `stop-service.sh` — stops processes using PID files in `run/` or falls back to pkill.

Usage:

Make the scripts executable if needed:

```bash
chmod +x scripts/*.sh
```

Then start or stop the services from the repository root:

```bash
./scripts/start-service.sh
./scripts/stop-service.sh
```

Notes:

- These scripts assume binaries live in `mod-host/` and `modhost-bridge/` subdirectories (as in the audio-host repo). Override paths with `MOD_HOST_BIN` and `MODHOST_BRIDGE_BIN` environment variables if needed.
- The scripts use `pw-jack` if available and if `USE_PWJACK=1` (default).
