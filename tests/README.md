# Marlise Integration Test Platform

This directory contains a comprehensive test platform for testing the Marlise system end-to-end across all architectural layers.

## Test Architecture

The test platform follows the same 4-layer architecture as Marlise itself:

```
Level 4: Client API HTTP Tests (test_04_client_api_http.py)
    ↕ HTTP/WebSocket
Level 3: Session Manager ZMQ Tests (test_03_session_manager_zmq.py)
    ↕ ZeroMQ RPC
Level 2: Session Manager Direct Tests (test_02_session_manager_direct.py)
    ↕ Direct calls (simulated)
Level 1: Mod-Host Bridge Direct Tests (test_01_modhost_bridge.py)
    ↕ ZeroMQ JSON-RPC
```

Each level builds upon the previous one, ensuring comprehensive coverage of the system.

## Quick Start

### 1. Health Check
First, verify the test environment works:
```bash
cd tests
./health_check.sh
```

### 2. Run All Tests
Run the complete test suite:
```bash
./run_integration_tests.sh
```

### 3. Run Specific Test Level
Run tests for a specific layer:
```bash
./run_integration_tests.sh --level1    # Mod-host bridge only
./run_integration_tests.sh --level2    # Session manager direct
./run_integration_tests.sh --level3    # Session manager ZMQ
./run_integration_tests.sh --level4    # Client API HTTP
```

## Test Environment

### Docker Components

The test environment includes:

- **Ubuntu 22.04** base with all dependencies
- **JACK dummy backend** (no real audio hardware needed)
- **LV2 plugins** (Calf, SWH, TAP, Invada for testing)
- **Complete Marlise stack** (mod-host, modhost-bridge, session-manager, client-interface)
- **Supervisor** for process management
- **Test runner** with pytest and all dependencies

### Known Test Plugins

The environment includes these guaranteed-available LV2 plugins:

```
# Calf plugins
http://calf.sourceforge.net/plugins/Reverb
http://calf.sourceforge.net/plugins/Delay
http://calf.sourceforge.net/plugins/Compressor
http://calf.sourceforge.net/plugins/Filter
http://calf.sourceforge.net/plugins/Equalizer5Band

# SWH plugins  
http://plugin.org.uk/swh-plugins/amp
http://plugin.org.uk/swh-plugins/lowpass_iir
http://plugin.org.uk/swh-plugins/delay_5s

# TAP plugins
http://moddevices.com/plugins/tap/reverb
http://moddevices.com/plugins/tap/chorus
```

## Test Framework

### Base Classes

- `MarliseTestClient`: Base class with common utilities
- `ModHostBridgeTestClient`: Direct ZMQ access to modhost-bridge
- `SessionManagerDirectTestClient`: Direct session manager calls
- `SessionManagerZmqTestClient`: ZMQ access to session manager
- `ClientApiTestClient`: HTTP API access with WebSocket support

### Fixtures

Pytest fixtures are provided for each test level:
- `modhost_bridge_client`
- `session_manager_direct_client` 
- `session_manager_zmq_client`
- `client_api_client`

## Test Levels in Detail

### Level 1: Mod-Host Bridge Direct
**File**: `test_01_modhost_bridge.py`  
**Purpose**: Test the lowest level audio engine communication  
**Coverage**:
- Plugin loading/removal via ZMQ
- Parameter control
- JACK status and port management
- Error handling
- Multiple plugin management

### Level 2: Session Manager Direct
**File**: `test_02_session_manager_direct.py`  
**Purpose**: Test business logic and state management  
**Coverage**:
- Plugin lifecycle management
- Audio connection management
- Snapshot operations
- System monitoring
- Configuration management

### Level 3: Session Manager ZMQ
**File**: `test_03_session_manager_zmq.py`  
**Purpose**: Test IPC layer and message serialization  
**Coverage**:
- ZMQ communication protocol
- Message integrity
- Batch operations
- Concurrent access
- Error propagation

### Level 4: Client API HTTP
**File**: `test_04_client_api_http.py`  
**Purpose**: Test complete end-to-end web API functionality  
**Coverage**:
- REST API endpoints
- WebSocket real-time updates
- HTTP error handling
- Content negotiation
- Complete workflow testing

## Test Data and Scenarios

### Plugin Test Scenarios
- Single plugin load/configure/remove
- Multiple plugin management
- Plugin parameter updates
- Plugin connections
- Error conditions (invalid plugins, parameters)

### System Test Scenarios  
- Resource monitoring (CPU, memory, disk)
- JACK audio system integration
- Configuration persistence
- Snapshot management
- Session lifecycle

### Integration Test Scenarios
- Complete pedalboard creation workflow
- Real-time parameter updates via WebSocket
- Concurrent client access
- System recovery after failures

## Running Tests

### Prerequisites
- Docker and docker-compose
- Network access for image building
- At least 4GB RAM for test environment

### Environment Variables
- `MARLISE_TEST_HOST`: Test environment hostname (default: localhost)
- `MARLISE_TEST_PORT`: HTTP API port (default: 8080)

### Command Line Options
```bash
./run_integration_tests.sh [OPTIONS]

OPTIONS:
  --level1, --modhost-bridge    Run only Level 1 tests
  --level2, --session-direct    Run only Level 2 tests  
  --level3, --session-zmq       Run only Level 3 tests
  --level4, --client-api        Run only Level 4 tests
  --no-build                    Skip Docker image building
  --show-logs                   Show service logs on failure
  --help                        Show help
```

### Output
- Test results: `test-results/`
- Service logs: `logs/`
- JUnit XML reports: `test-results/junit/`

## Debugging

### Service Logs
Service logs are available in the `logs/` directory:
- `jack-dummy.log`: JACK dummy backend
- `mod-host.log`: mod-host audio processor
- `modhost-bridge.log`: Bridge component
- `session-manager.log`: Session manager
- `client-interface.log`: HTTP API server

### Interactive Debugging
Access the test environment interactively:
```bash
cd tests
docker-compose -f docker/docker-compose.test.yml exec marlise-test-env bash
```

### Manual Testing
Test individual components manually:
```bash
# Test HTTP API
curl http://localhost:8080/health

# Test ZMQ (requires zmq tools)
python3 -c "
import zmq
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5718')
socket.send_json({'method': 'get_session_status', 'params': {}, 'id': 1})
print(socket.recv_json())
"
```

## Continuous Integration

The test platform is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        run: |
          cd tests
          ./run_integration_tests.sh
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: tests/test-results/
```

## Performance Testing

The test framework supports performance testing:
- Concurrent request handling
- Plugin loading/unloading speed
- Memory usage under load
- WebSocket message throughput

## Extending Tests

### Adding New Test Cases
1. Add test methods to existing test classes
2. Use appropriate client fixture for the test level
3. Follow naming convention: `test_<functionality>_<level>`
4. Add proper cleanup in `finally` blocks

### Adding New Test Plugins
1. Update `test-plugins.txt` with new URIs
2. Ensure plugins are available in Docker image
3. Update `TEST_PLUGINS` list in test framework

### Custom Test Environments
1. Modify `docker/Dockerfile.test-environment`
2. Update supervisor configuration as needed
3. Rebuild with `--no-build` to force rebuild

## Troubleshooting

### Common Issues

**Services not starting**: Check Docker resources and port availability
**Plugin loading fails**: Verify LV2 plugins are installed in container
**ZMQ timeouts**: Increase timeout values in test framework
**HTTP connection refused**: Ensure all services started successfully

### Debug Mode
Run with verbose output and logs:
```bash
./run_integration_tests.sh --show-logs
```

### Clean Environment
Reset the test environment:
```bash
docker-compose -f docker/docker-compose.test.yml down -v
docker system prune -f
```