#!/usr/bin/env bash
set -euo pipefail

# Stop services started by start-service.sh

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
RUN_DIR="$ROOT_DIR/run"
LOG_DIR="$ROOT_DIR/logs"

if [ ! -d "$RUN_DIR" ]; then
    echo "No run directory found ($RUN_DIR). Trying to stop by process name..."
    pkill -f "modhost-bridge" || true
    pkill -f "mod-host" || true
    pkill -f "session-manager" || true
    exit 0
fi

stop_pidfile() {
    local pf="$1"
    if [ -f "$pf" ]; then
        pid=$(cat "$pf" 2>/dev/null || true)
        if [ -n "$pid" ]; then
            if kill -0 "$pid" 2>/dev/null; then
                echo "Stopping PID $pid from $pf"
                kill "$pid" 2>/dev/null || true
                # wait up to 5s for graceful stop
                for i in {1..5}; do
                    if ! kill -0 "$pid" 2>/dev/null; then
                        break
                    fi
                    sleep 1
                done
                if kill -0 "$pid" 2>/dev/null; then
                    echo "PID $pid did not exit; killing..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
            else
                echo "Process $pid not running (from $pf)"
            fi
        fi
        rm -f "$pf"
    fi
}

stop_pidfile "$RUN_DIR/session-manager.pid"
stop_pidfile "$RUN_DIR/modhost-bridge.pid"
stop_pidfile "$RUN_DIR/mod-host.pid"

echo "Stopped services listed in $RUN_DIR (if any)."

# As fallback ensure processes are not running
pkill -f "modhost-bridge" || true
pkill -f "mod-host" || true
pkill -f "session-manager" || true

echo "Done. Logs are in $LOG_DIR"

exit 0
