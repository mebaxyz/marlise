#!/usr/bin/env bash
set -euo pipefail

# Entrypoint for the audio-engine image.
# If JACK_DUMMY=1 or JACK_DUMMY=true this will start a dummy jackd before
# invoking the repository start-service.sh which starts mod-host and modhost-bridge.

LOG_PREFIX="[marlise-entrypoint]"
function log(){ echo "${LOG_PREFIX} $@"; }

# Ensure bundled libraries are visible to child processes
export LD_LIBRARY_PATH="/opt/marlise/lib:${LD_LIBRARY_PATH:-}"

# Default ZeroMQ bridge endpoints to bind on all interfaces so health is reachable
export MODHOST_BRIDGE_REP="${MODHOST_BRIDGE_REP:-tcp://0.0.0.0:${MODHOST_BRIDGE_PORT:-6000}}"
export MODHOST_BRIDGE_PUB="${MODHOST_BRIDGE_PUB:-tcp://0.0.0.0:${MODHOST_BRIDGE_PUB_PORT:-6001}}"
export MODHOST_BRIDGE_HEALTH="${MODHOST_BRIDGE_HEALTH:-tcp://0.0.0.0:${MODHOST_BRIDGE_HEALTH_PORT:-6002}}"

JACK_DUMMY=${JACK_DUMMY:-0}
JACK_DEVICE=${JACK_DEVICE:-hw:0}

if [ "${JACK_DUMMY}" = "1" ] || [ "${JACK_DUMMY}" = "true" ]; then
  log "JACK_DUMMY set -> starting JACK dummy server"
  # Start JACK dummy in background (keep logs under /opt/logs if present)
  mkdir -p /opt/logs
  jackd -d dummy -r 48000 -p 256 -P 2 -C 2 >/opt/logs/jack.log 2>&1 &
  JACKD_PID=$!
  log "Started jackd (PID=${JACKD_PID}), waiting briefly for it to initialize"
  sleep 1
  if ! command -v jack_lsp >/dev/null 2>&1 || ! jack_lsp >/dev/null 2>&1; then
    log "WARNING: jack_lsp failed. JACK may not be fully operational. Continuing anyway."
  fi
else
  log "JACK_DUMMY not set -> not starting jackd automatically"
fi

log "Starting modhost-bridge"
# Optionally skip starting the in-container bridge (useful when running tests
# with an external bridge or host networking where another bridge is already
# running). Set SKIP_BRIDGE_IN_CONTAINER=1 or "true" to skip.
if [ "${SKIP_BRIDGE_IN_CONTAINER:-0}" = "1" ] || [ "${SKIP_BRIDGE_IN_CONTAINER:-0}" = "true" ]; then
  log "SKIP_BRIDGE_IN_CONTAINER set -> skipping in-container modhost-bridge startup"
else
  # Start modhost-bridge in background (health monitor now binds early inside the bridge)
  # Export environment variables for the bridge process
  export MODHOST_BRIDGE_REP MODHOST_BRIDGE_PUB MODHOST_BRIDGE_HEALTH
  /opt/marlise/bin/modhost-bridge --port ${MODHOST_BRIDGE_PORT:-6000} >/opt/logs/modhost-bridge.log 2>&1 &
  BRIDGE_PID=$!
  log "modhost-bridge PID=${BRIDGE_PID} started"

  # If requested, dump a short debug snapshot of network listeners for easier tracing
  if [ "${BRIDGE_DEBUG:-0}" = "1" ] || [ "${BRIDGE_DEBUG:-0}" = "true" ]; then
    log "BRIDGE_DEBUG set -> dumping socket listeners to /opt/logs/modhost-bridge.net.log"
    ss -tlnp 2>/dev/null || true
    ss -tlnp > /opt/logs/modhost-bridge.net.log 2>&1 || true
    env | sort > /opt/logs/modhost-bridge.env.log || true
  fi
fi

log "Starting mod-host as PID1"
# Exec mod-host as the main container process
exec /opt/marlise/bin/mod-host -n -p ${MOD_HOST_PORT:-5555} -f ${MOD_HOST_FEEDBACK_PORT:-5556} -v
