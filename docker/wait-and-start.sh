#!/bin/sh
# wait-and-start.sh - POSIX shell compatible
# Waits for target services before starting nginx
# Expects env var WAIT_FOR_TARGETS as comma-separated list of host:port or http://... URLs

set -e

if [ -n "${WAIT_FOR_TARGETS:-}" ]; then
  # Split on commas (POSIX compatible)
  OLD_IFS="$IFS"
  IFS=','
  for t in $WAIT_FOR_TARGETS; do
    # Trim leading/trailing spaces
    tt=$(echo "$t" | sed 's/^ *//; s/ *$//')
    if echo "$tt" | grep -qE '^https?://'; then
      echo "Waiting for HTTP $tt"
      /usr/local/bin/wait-for.sh --http "$tt" --timeout ${WAIT_FOR_TIMEOUT:-30} --interval ${WAIT_FOR_INTERVAL:-1}
    else
      host=$(echo "$tt" | cut -d: -f1)
      port=$(echo "$tt" | cut -d: -f2)
      echo "Waiting for TCP $host:$port"
      /usr/local/bin/wait-for.sh "$host" "$port" --timeout ${WAIT_FOR_TIMEOUT:-30} --interval ${WAIT_FOR_INTERVAL:-1}
    fi
  done
  IFS="$OLD_IFS"
else
  echo "No WAIT_FOR_TARGETS set; starting nginx immediately"
fi

# exec the passed command (the default CMD will be run by docker-entrypoint.sh)
exec "$@"
