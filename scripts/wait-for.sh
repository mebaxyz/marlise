#!/usr/bin/env bash
# wait-for.sh - wait for a TCP host:port or HTTP URL to become available
# Usage:
#   wait-for.sh host port [--timeout SECONDS] [--interval SECONDS]
#   wait-for.sh --http URL [--timeout SECONDS] [--interval SECONDS]

set -euo pipefail

TIMEOUT=30
INTERVAL=1

show_help() {
  cat <<EOF
Usage:
  $0 host port [--timeout SECONDS] [--interval SECONDS]
  $0 --http URL [--timeout SECONDS] [--interval SECONDS]

Options:
  --timeout SECONDS   Maximum seconds to wait (default: ${TIMEOUT})
  --interval SECONDS  Seconds between attempts (default: ${INTERVAL})
EOF
}

if [ "$#" -lt 1 ]; then
  show_help
  exit 2
fi

MODE="tcp"
HOST=""
PORT=""
URL=""

if [ "$1" = "--http" ]; then
  MODE="http"
  shift
  URL="$1"
  shift
else
  HOST="$1"
  PORT="$2"
  shift 2
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --timeout)
      TIMEOUT="$2"; shift 2;;
    --interval)
      INTERVAL="$2"; shift 2;;
    -h|--help)
      show_help; exit 0;;
    *)
      echo "Unknown option: $1"; show_help; exit 2;;
  esac
done

start_ts=$(date +%s)
end_ts=$((start_ts + TIMEOUT))

if [ "$MODE" = "http" ]; then
  target="$URL"
else
  target="${HOST}:${PORT}"
fi
echo "Waiting for ${MODE} ${target} (timeout=${TIMEOUT}s, interval=${INTERVAL}s)..."

check_tcp() {
  # Use /dev/tcp if available
  if command -v nc >/dev/null 2>&1; then
    nc -z "$HOST" "$PORT" >/dev/null 2>&1
    return $?
  fi
  if [ -e /dev/tcp/"$HOST"/"$PORT" ]; then
    # bash built-in test by attempting redirect
    (echo >/dev/tcp/"$HOST"/"$PORT") >/dev/null 2>&1 && return 0 || return 1
  fi
  # Fallback: try curl with connect timeout
  if command -v curl >/dev/null 2>&1; then
    curl --connect-timeout 2 -sS "http://$HOST:$PORT/" >/dev/null 2>&1 && return 0 || return 1
  fi
  return 1
}

check_http() {
  if command -v curl >/dev/null 2>&1; then
    status=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 2 "$URL" || true)
    [ "$status" = "200" ] && return 0 || return 1
  else
    # If curl isn't available, attempt a TCP connect
    hostport=$(echo "$URL" | sed -E 's#^https?://([^/]+).*#\1#')
    host=$(echo "$hostport" | sed -E 's#:(.*)##')
    port=$(echo "$hostport" | sed -nE 's#.*:(.*)#\1#p')
    if [ -z "$port" ]; then
      port=80
    fi
    HOST="$host"; PORT="$port"
    check_tcp
    return $?
  fi
}

while true; do
  now=$(date +%s)
  if [ $now -gt $end_ts ]; then
    echo "Timed out after ${TIMEOUT} seconds waiting for ${MODE}."
    exit 1
  fi

  if [ "$MODE" = "http" ]; then
    if check_http; then
      echo "HTTP target is available: $URL"
      exit 0
    fi
  else
    if check_tcp; then
      echo "TCP target is available: ${HOST}:${PORT}"
      exit 0
    fi
  fi

  sleep "$INTERVAL"
done
