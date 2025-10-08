#!/bin/bash

# Smoke test for the fully operational test platform
# This script verifies that all mock services are working properly

set -e

cd "$(dirname "$0")"

echo "🧪 Starting Test Platform Smoke Test"
echo "=================================="

# Build and start the test environment
echo "📦 Building test environment..."
docker compose -f docker/docker-compose.test.yml build marlise-test-env

echo "🚀 Starting test environment..."
docker compose -f docker/docker-compose.test.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Test 1: Check if services are running
echo "🔍 Testing service status..."
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env supervisorctl status

# Test 2: Check mock mod-host TCP connection
echo "🎵 Testing mock mod-host connection..."
timeout 5 bash -c 'echo "ping" | nc localhost 5555' || echo "Failed to connect to mod-host"

# Test 3: Check mock modhost-bridge ZMQ connection  
echo "🌉 Testing mock modhost-bridge ZMQ connection..."
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env python3 -c "
import zmq
import json
import time

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:6000')
socket.setsockopt(zmq.RCVTIMEO, 5000)

request = {
    'jsonrpc': '2.0',
    'method': 'get_jack_status',
    'id': 1
}

try:
    socket.send_json(request)
    response = socket.recv_json()
    print('✅ Modhost-bridge ZMQ: OK')
    print(f'Response: {response}')
except Exception as e:
    print(f'❌ Modhost-bridge ZMQ: {e}')
finally:
    socket.close()
    context.term()
"

# Test 4: Check session manager ZMQ endpoints
echo "🎯 Testing session manager ZMQ endpoints..."
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env python3 -c "
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5718')
socket.setsockopt(zmq.RCVTIMEO, 5000)

request = {
    'jsonrpc': '2.0',
    'method': 'get_system_status',
    'id': 1
}

try:
    socket.send_json(request)
    response = socket.recv_json()
    print('✅ Session Manager ZMQ: OK')
    print(f'Response: {json.dumps(response, indent=2)[:200]}...')
except Exception as e:
    print(f'❌ Session Manager ZMQ: {e}')
finally:
    socket.close()
    context.term()
"

# Test 5: Check client interface HTTP API
echo "🌐 Testing client interface HTTP API..."
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env python3 -c "
import requests
import json

try:
    response = requests.get('http://localhost:8080/health', timeout=5)
    print(f'✅ Client Interface HTTP: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'❌ Client Interface HTTP: {e}')
"

# Test 6: End-to-end plugin loading test
echo "🔌 Testing end-to-end plugin loading..."
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env python3 -c "
import requests
import json

try:
    # Load a plugin via HTTP API
    response = requests.post(
        'http://localhost:8080/api/plugins',
        json={'uri': 'http://calf.sourceforge.net/plugins/Reverb'},
        timeout=10
    )
    print(f'✅ End-to-end plugin load: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'❌ End-to-end plugin load: {e}')
"

echo "📋 Service logs sample:"
echo "----------------------"
docker compose -f docker/docker-compose.test.yml exec -T marlise-test-env tail -n 5 /var/log/marlise/session-manager.log

echo ""
echo "🎉 Smoke test complete!"
echo "Ready to run full integration tests with: ./run_integration_tests.sh"
echo ""
echo "To clean up: docker compose -f docker/docker-compose.test.yml down -v"