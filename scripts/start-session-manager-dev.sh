#!/bin/bash

set -euo pipefail

# Try to stop a locally running session-manager if it's present
PID_FILE="$(pwd)/run/session-manager.pid"

echo "Checking for locally running session-manager..."
if [ -f "$PID_FILE" ]; then
  PID=$(sed -n '1p' "$PID_FILE" | tr -d '[:space:]' || true)
  if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
    echo "Found session-manager running with PID $PID. Killing..."
    kill "$PID" || true
    sleep 1
    if ps -p "$PID" > /dev/null 2>&1; then
      echo "PID $PID still alive, sending SIGTERM..."
      kill -TERM "$PID" || true
    fi
  fi
else
  # Fallback: try to find a python process running main.py
  PMATCH=$(pgrep -f "session-manager/main.py" || true)
  if [ -n "$PMATCH" ]; then
    echo "Found session-manager process(es): $PMATCH. Killing..."
    kill $PMATCH || true
  else
    echo "No local session-manager process found."
  fi
fi

echo "Starting session-manager container via docker compose..."
docker compose -f /home/nicolas/project/marlise/docker/docker-compose.dev.yml up -d --build session-manager

echo "Done. Container started."
