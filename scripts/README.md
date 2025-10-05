Scripts to start and stop the Marlise audio system components.

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

- These scripts assume binaries live in `audio-engine/mod-host/` and `audio-engine/modhost-bridge/` subdirectories. Override paths with `MOD_HOST_BIN` and `MODHOST_BRIDGE_BIN` environment variables if needed.
- The session manager is started from `session-manager/`. Override with `SESSION_MANAGER_SCRIPT` if needed.
- The scripts use `pw-jack` if available and if `USE_PWJACK=1` (default).
