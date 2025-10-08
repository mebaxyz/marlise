#!/usr/bin/env bash
set -euo pipefail

# Start service launcher: start mod-host, wait for it to accept connections, then start modhost-bridge
# Writes PID files under $ROOT_DIR/run so the stop script can gracefully stop the services.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"
RUN_DIR="$ROOT_DIR/run"
mkdir -p "$LOG_DIR" "$RUN_DIR"

# Configuration (override with env vars)
MOD_HOST_BIN=${MOD_HOST_BIN:-"$ROOT_DIR/audio-engine/mod-host/mod-host"}
if [ ! -x "$MOD_HOST_BIN" ]; then
    MOD_HOST_BIN="$ROOT_DIR/audio-engine/mod-host/src/mod-host"
fi
MODHOST_BRIDGE_BIN=${MODHOST_BRIDGE_BIN:-"$ROOT_DIR/audio-engine/modhost-bridge/build/modhost-bridge"}
if [ ! -x "$MODHOST_BRIDGE_BIN" ]; then
    MODHOST_BRIDGE_BIN="$ROOT_DIR/audio-engine/modhost-bridge/modhost-bridge"
fi

USE_PWJACK=${USE_PWJACK:-1}
PWJACK_CMD=""
if [ "${USE_PWJACK}" -eq 1 ] && command -v pw-jack >/dev/null 2>&1; then
    PWJACK_CMD="pw-jack"
fi

MOD_HOST_PORT=${MOD_HOST_PORT:-5555}
MOD_HOST_FEEDBACK_PORT=${MOD_HOST_FEEDBACK_PORT:-5556}
WAIT_TIMEOUT=${WAIT_TIMEOUT:-30}
SLEEP_INTERVAL=${SLEEP_INTERVAL:-1}

MOD_HOST_ARGS=${MOD_HOST_ARGS:-"-n -p ${MOD_HOST_PORT} -f ${MOD_HOST_FEEDBACK_PORT} -v"}
BRIDGE_ARGS=${BRIDGE_ARGS:-""}

start_with_optional_pwjack() {
    local bin="$1"; shift
    local log="$1"; shift
    local args=("$@")
    if [ -n "$PWJACK_CMD" ]; then
        echo "Starting via pw-jack: $bin ${args[*]} (log: $log)"
        $PWJACK_CMD "$bin" "${args[@]}" &> "$log" &
    else
        echo "Starting: $bin ${args[*]} (log: $log)"
        "$bin" "${args[@]}" &> "$log" &
    fi
    echo $!
}

start_without_pwjack() {
    local bin="$1"; shift
    local log="$1"; shift
    local args=("$@")
    echo "Starting: $bin ${args[*]} (log: $log)"
    "$bin" "${args[@]}" &> "$log" &
    echo $!
}

wait_for_port() {
    local host="$1"; local port="$2"; local timeout="$3"
    local start_ts=$(date +%s)
    while true; do
        if (echo > /dev/tcp/"$host"/"$port") >/dev/null 2>&1; then
            return 0
        fi
        if [ $(( $(date +%s) - start_ts )) -ge "$timeout" ]; then
            return 1
        fi
        sleep "$SLEEP_INTERVAL"
    done
}

if [ ! -x "$MOD_HOST_BIN" ]; then
    echo "Error: mod-host binary not found or not executable: $MOD_HOST_BIN" >&2
    exit 1
fi
if [ ! -x "$MODHOST_BRIDGE_BIN" ]; then
    echo "Error: modhost-bridge binary not found or not executable: $MODHOST_BRIDGE_BIN" >&2
    exit 1
fi

MOD_HOST_LOG="$LOG_DIR/mod-host.log"
BRIDGE_LOG="$LOG_DIR/modhost-bridge.log"

echo "Starting mod-host -> waiting for port ${MOD_HOST_PORT} -> then starting modhost-bridge"

modhost_pid=$(start_with_optional_pwjack "$MOD_HOST_BIN" "$MOD_HOST_LOG" $MOD_HOST_ARGS)
echo "mod-host PID: $modhost_pid (log: $MOD_HOST_LOG)"
echo "$modhost_pid" > "$RUN_DIR/mod-host.pid"

echo "Waiting up to ${WAIT_TIMEOUT}s for mod-host to accept connections on ${MOD_HOST_PORT}..."
if ! wait_for_port "127.0.0.1" "$MOD_HOST_PORT" "$WAIT_TIMEOUT"; then
    echo "Error: mod-host did not become available on port ${MOD_HOST_PORT} within ${WAIT_TIMEOUT}s" >&2
    echo "Check logs: $MOD_HOST_LOG" >&2
    kill "$modhost_pid" 2>/dev/null || true
    rm -f "$RUN_DIR/mod-host.pid"
    exit 1
fi

echo "mod-host is reachable on ${MOD_HOST_PORT}"

# Set mod-host connection to use 127.0.0.1 for bridge
export MOD_HOST_HOST=127.0.0.1
modbridge_pid=$(start_without_pwjack "$MODHOST_BRIDGE_BIN" "$BRIDGE_LOG" $BRIDGE_ARGS)
echo "modhost-bridge PID: $modbridge_pid (log: $BRIDGE_LOG)"
echo "$modbridge_pid" > "$RUN_DIR/modhost-bridge.pid"

echo "Started: mod-host=${modhost_pid}, modhost-bridge=${modbridge_pid}"
echo "Logs: mod-host -> $MOD_HOST_LOG ; bridge -> $BRIDGE_LOG"

# Start session-manager (optional: used to test clients)
# You can override with SESSION_MANAGER_SCRIPT env var.
SESSION_MANAGER_SCRIPT=${SESSION_MANAGER_SCRIPT:-"$ROOT_DIR/session_manager/start_session_manager.sh"}
SESSION_LOG="$LOG_DIR/session-manager.log"
SESSION_WAIT_TIMEOUT=${SESSION_WAIT_TIMEOUT:-10}

if [ -x "$SESSION_MANAGER_SCRIPT" ]; then
    echo "Starting session-manager using: $SESSION_MANAGER_SCRIPT (log: $SESSION_LOG)"
    # Start session manager (it sets its own PYTHONPATH relative to its script dir)
    "$SESSION_MANAGER_SCRIPT" &> "$SESSION_LOG" &
    session_pid=$!
    echo "$session_pid" > "$RUN_DIR/session-manager.pid"

    # Quick wait to ensure the process didn't immediately exit
    start_ts=$(date +%s)
    while true; do
        if ! kill -0 "$session_pid" 2>/dev/null; then
            echo "Error: session-manager (PID $session_pid) exited shortly after starting. Check $SESSION_LOG" >&2
            rm -f "$RUN_DIR/session-manager.pid"
            break
        fi
        if [ $(( $(date +%s) - start_ts )) -ge "$SESSION_WAIT_TIMEOUT" ]; then
            echo "session-manager appears to be running (PID $session_pid)"
            break
        fi
        sleep 1
    done
else
    echo "Warning: session-manager start script not found or not executable: $SESSION_MANAGER_SCRIPT. Skipping session-manager start." >&2
fi

echo "PID files written to: $RUN_DIR"
printf "%s\n" "MOD_HOST_PID=${modhost_pid}" "MODHOST_BRIDGE_PID=${modbridge_pid}" "SESSION_MANAGER_PID=${session_pid:-}" 

exit 0
