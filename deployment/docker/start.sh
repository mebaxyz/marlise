#!/bin/bash
set -euo pipefail

# start.sh - entrypoint for mod-host + modhost-bridge container
# Expects the following optional environment variables:
# - JACK_DEVICE (default: hw:0)  - ALSA device to bind JACK
# - JACK_CLIENT_NAME (default: marlise-jack)
# - MODHOST_BRIDGE_PORT (default: 6000)
# - MOD_HOST_CMD (default: /opt/marlise/bin/mod-host)
# - MODHOST_BRIDGE_CMD (default: /opt/marlise/bin/modhost-bridge)

JACK_DEVICE=${JACK_DEVICE:-hw:0}
JACK_CLIENT_NAME=${JACK_CLIENT_NAME:-marlise-jack}
MODHOST_BRIDGE_PORT=${MODHOST_BRIDGE_PORT:-6000}
MOD_HOST_CMD=${MOD_HOST_CMD:-/opt/marlise/bin/mod-host}
MODHOST_BRIDGE_CMD=${MODHOST_BRIDGE_CMD:-/opt/marlise/bin/modhost-bridge}

LOG_PREFIX="[marlise-start]"

function log() { echo "${LOG_PREFIX} $@"; }

trap 'log "Shutting down..."; kill -TERM "${JACKD_PID:-}" 2>/dev/null || true; kill -TERM "${BRIDGE_PID:-}" 2>/dev/null || true; kill -TERM "${MODHOST_PID:-}" 2>/dev/null || true; wait' SIGTERM SIGINT

log "Starting JACK with device=${JACK_DEVICE}"
# Start JACK in the background; use -P to allow realtime on systems with proper caps
jackd -d alsa -d ${JACK_DEVICE} -P -p 1024 -n 2 &
JACKD_PID=$!
sleep 0.5

log "Checking JACK status"
if ! jack_lsp >/dev/null 2>&1; then
  log "WARNING: jackd may not be running properly. jack_lsp failed. Continuing anyway."
fi

# Start modhost-bridge if available
if [ -x "${MODHOST_BRIDGE_CMD}" ]; then
  log "Starting modhost-bridge on port ${MODHOST_BRIDGE_PORT}"
  "${MODHOST_BRIDGE_CMD}" --port ${MODHOST_BRIDGE_PORT} &
  BRIDGE_PID=$!
else
  log "modhost-bridge not found at ${MODHOST_BRIDGE_CMD}. Skipping."
fi

# Start mod-host if available
if [ -x "${MOD_HOST_CMD}" ]; then
  log "Starting mod-host"
  "${MOD_HOST_CMD}" &
  MODHOST_PID=$!
else
  log "mod-host not found at ${MOD_HOST_CMD}. Skipping."
fi

log "Services started. Waiting for processes..."

wait -n
log "One process exited, shutting down container"
