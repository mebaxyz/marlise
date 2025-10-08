#!/bin/bash
# Start JACK with dummy backend for testing

set -e

echo "Starting JACK dummy backend for testing..."

# Kill any existing JACK processes
pkill -f jackd || true
sleep 2

# Start JACK with dummy backend
# -d dummy: Use dummy backend (no real audio hardware needed)
# -r 48000: Sample rate
# -p 512: Buffer size
# -n 2: Number of periods
exec jackd -d dummy -r 48000 -p 512 -n 2 &

# Wait a bit for JACK to start
sleep 3

# Verify JACK is running
if ! pgrep jackd > /dev/null; then
    echo "ERROR: JACK failed to start"
    exit 1
fi

echo "JACK dummy backend started successfully"

# Create some test ports for connection testing
jack_lsp || echo "JACK not fully ready yet"

# Keep the script running
wait