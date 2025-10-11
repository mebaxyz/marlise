#!/usr/bin/env bash
set -euo pipefail

# Entrypoint for the audio-engine image.
# If JACK_DUMMY=1 or JACK_DUMMY=true this will start a dummy jackd before
# invoking the repository start-service.sh which starts mod-host and modhost-bridge.

LOG_PREFIX="[marlise-entrypoint]"
function log(){ echo "${LOG_PREFIX} $@"; }

# Ensure bundled libraries are visible to child processes
export LD_LIBRARY_PATH="/opt/marlise/lib:${LD_LIBRARY_PATH:-}"

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
# Start modhost-bridge in background
/opt/marlise/bin/modhost-bridge --port ${MODHOST_BRIDGE_PORT:-6000} >/opt/logs/modhost-bridge.log 2>&1 &
BRIDGE_PID=$!
log "modhost-bridge PID=${BRIDGE_PID} started"

log "Starting mod-host as PID1"
# Exec mod-host as the main container process
exec /opt/marlise/bin/mod-host -n -p ${MOD_HOST_PORT:-5555} -f ${MOD_HOST_FEEDBACK_PORT:-5556} -v
