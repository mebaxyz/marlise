#!/bin/sh
# Ensure mounted data directory is writable by the dev user
set -e
DATA_DIR=/app/data
if [ -d "$DATA_DIR" ]; then
  # Try to change ownership if possible (may fail if not permitted)
  chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
  # Make settings file readable/writable by the dev user if possible
  if [ -f "$DATA_DIR/settings.json" ]; then
    chmod 0644 "$DATA_DIR/settings.json" 2>/dev/null || true
    chown 1000:1000 "$DATA_DIR/settings.json" 2>/dev/null || true
  fi
else
  mkdir -p "$DATA_DIR"
  chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
fi
# Exec the command as the current user (we're already running as UID 1000)
exec "$@"
