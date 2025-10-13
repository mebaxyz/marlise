#!/bin/bash
# Debug script to capture bridge logs during test execution

set -e

# Start test in background
cd /home/nicolas/xx_work/marlise
tests/.venv-integration/bin/pytest tests/integration/test_modhost_bridge_full.py::test_two_plugins_chain_and_jack_connections -xvs 2>&1 > /tmp/test_output.log &
TEST_PID=$!

# Wait for container to start
sleep 3

# Find the container
CONTAINER_ID=$(docker ps | grep marlise-audio | head -1 | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "No container found yet, waiting longer..."
    sleep 2
    CONTAINER_ID=$(docker ps -a | grep marlise-audio | head -1 | awk '{print $1}')
fi

if [ -n "$CONTAINER_ID" ]; then
    echo "Found container: $CONTAINER_ID"
    # Wait for test to actually try to connect
    sleep 2
    echo "===== MODHOST-BRIDGE LOGS ====="
    docker exec "$CONTAINER_ID" cat /opt/logs/modhost-bridge.log 2>&1 || echo "No bridge log file"
    echo "===== END BRIDGE LOGS ====="
fi

# Wait for test to complete
wait $TEST_PID || true

echo "===== TEST OUTPUT (last 50 lines) ====="
tail -50 /tmp/test_output.log
