#!/bin/bash
# Quick test for checking if the test environment is working

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Marlise Test Environment Health Check"
echo "======================================="

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Start minimal environment
echo "Starting test environment..."
$DOCKER_COMPOSE -f docker/docker-compose.test.yml up -d marlise-test-env

echo "Waiting for services..."
sleep 20

echo "Checking service status:"
$DOCKER_COMPOSE -f docker/docker-compose.test.yml ps

echo -e "\nChecking service logs:"
$DOCKER_COMPOSE -f docker/docker-compose.test.yml logs --tail=20 marlise-test-env

echo -e "\nTesting basic connectivity:"

# Test HTTP endpoint
if curl -f http://localhost:8080/health 2>/dev/null; then
    echo "✅ HTTP API is responding"
else
    echo "❌ HTTP API is not responding"
fi

# Test ZMQ ports
if nc -z localhost 5718 2>/dev/null; then
    echo "✅ Session Manager ZMQ port is open"
else
    echo "❌ Session Manager ZMQ port is not accessible"
fi

if nc -z localhost 6000 2>/dev/null; then
    echo "✅ Modhost Bridge ZMQ port is open"
else
    echo "❌ Modhost Bridge ZMQ port is not accessible"
fi

if nc -z localhost 5555 2>/dev/null; then
    echo "✅ mod-host command port is open"
else  
    echo "❌ mod-host command port is not accessible"
fi

echo -e "\nRunning a quick smoke test..."
$DOCKER_COMPOSE -f docker/docker-compose.test.yml run --rm marlise-test-runner \
    python3 -c "
import requests
import zmq
import json

print('Testing HTTP endpoint...')
try:
    response = requests.get('http://marlise-test-env:8080/health', timeout=5)
    print(f'HTTP Status: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'HTTP Error: {e}')

print('\nTesting ZMQ endpoint...')
try:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
    socket.connect('tcp://marlise-test-env:5718')
    
    request = {'method': 'get_session_status', 'params': {}, 'id': 1}
    socket.send_json(request)
    response = socket.recv_json()
    print(f'ZMQ Response: {response}')
    
    socket.close()
    context.term()
except Exception as e:
    print(f'ZMQ Error: {e}')

print('\n✅ Smoke test completed')
"

echo -e "\n🏁 Health check completed"
echo "You can now run the full test suite with: ./run_integration_tests.sh"

# Cleanup
echo "Stopping test environment..."
$DOCKER_COMPOSE -f docker/docker-compose.test.yml down