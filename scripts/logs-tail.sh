#!/usr/bin/env bash
# Tail all Marlise service logs simultaneously

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "No logs directory found at $LOG_DIR"
    exit 1
fi

echo "📋 Tailing all Marlise logs..."
echo "Press Ctrl+C to stop"
echo ""

# Use multitail if available, otherwise fall back to tail
if command -v multitail &> /dev/null; then
    multitail \
        -ci green -l "tail -f $LOG_DIR/mod-host.log" \
        -ci blue -l "tail -f $LOG_DIR/modhost-bridge.log" \
        -ci yellow -l "tail -f $LOG_DIR/session-manager.log"
else
    # Fall back to regular tail with prefixes
    tail -f \
        "$LOG_DIR/mod-host.log" \
        "$LOG_DIR/modhost-bridge.log" \
        "$LOG_DIR/session-manager.log" 2>/dev/null | \
    awk '{
        if (FILENAME ~ /mod-host/) print "\033[32m[MOD-HOST]\033[0m", $0
        else if (FILENAME ~ /bridge/) print "\033[34m[BRIDGE]\033[0m", $0
        else if (FILENAME ~ /session/) print "\033[33m[SESSION]\033[0m", $0
        else print $0
    }'
fi
