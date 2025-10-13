# Copilot Instructions for Marlise

## Project Overview

**Marlise** is a fork of [MOD-UI](https://github.com/moddevices/mod-ui), a web-based audio effects pedalboard interface for MOD audio devices. This fork uses a simplified, high-performance architecture with direct ZeroMQ communication for real-time audio processing.

### Key Technologies
- **Python 3.8+** with asyncio (backend services)
- **FastAPI** (web API framework)
- **ZeroMQ** (inter-process communication)
- **C++** (audio bridge component)
- **JACK Audio** or PipeWire (audio server)
- **LV2 plugins** (audio effects)

### Project Structure
```
marlise/
├── audio-engine/        # Low-level audio processing
│   ├── mod-host/        # LV2 plugin host (C)
│   └── modhost-bridge/  # JSON-RPC bridge (C++)
├── session-manager/     # High-level orchestration (Python)
│   └── src/             # Session manager source code
├── client-interface/    # Web API and UI (FastAPI)
│   ├── api/             # FastAPI backend
│   └── web/             # Web client
├── scripts/             # Service management scripts
│   ├── start-service.sh # Start all services
│   └── stop-service.sh  # Stop all services
├── docs/                # Documentation
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── COMMUNICATION_ARCHITECTURE.md
│   ├── COMMUNICATION_FLOW_DIAGRAMS.md
│   └── COMMUNICATION_QUICK_REFERENCE.md
├── tests/               # Comprehensive integration test platform
│   ├── docker/          # Docker test environment
│   ├── integration/     # Multi-layer test suites
│   ├── run_integration_tests.sh  # Main test runner
│   ├── health_check.sh  # Environment verification
│   └── README.md        # Test platform documentation
├── STRUCTURE.md         # Quick structure reference
└── README.md            # Project documentation
```

## Recent changes

- [Unreleased] - 2025-10-14
    - modhost-bridge: delegate JACK connect/disconnect commands to mod-host and expose numeric `host_instance`.
    - Bridge: auto-initialize JACK at startup and add integration test that validates plugin chaining and JACK connections.

> NOTE: When you change code or add features, please update the top-level `CHANGELOG.md` and this instructions file to reflect the changes. Keep docs and instructions in sync with code.

> TEST PLAN MAINTENANCE: When you add an integration test or expose a new RPC/handler, update the integration test plan file `tests/INTEGRATION_TEST_PLAN.md` and add an entry to this instructions file describing the new test. If you introduce a new public RPC or function that affects cross-process behavior, mark it as "untested" in the plan until a test is added. Consider adding a skipped (xfail) test to highlight missing coverage in CI.


## Architecture

The system uses a 4-layer architecture with ZeroMQ-based communication:

```
Web Client (Browser)
      ↕ HTTP/WebSocket
Client Interface (FastAPI on port 8080)
      ↕ ZeroMQ RPC + PubSub
Session Manager (Python service)
      ↕ ZeroMQ JSON-RPC
Modhost Bridge (C++ service)
      ↕ TCP Text Protocol
mod-host (LV2 Plugin Host)
```

### Component Responsibilities
1. **Client Interface**: REST API and WebSocket endpoints for browser interaction
2. **Session Manager**: High-level business logic and state management
3. **Modhost Bridge**: Protocol translation (JSON-RPC ↔ mod-host text protocol)
4. **mod-host**: Real-time audio processing with LV2 plugins

### Communication Ports
- `8080`: Client Interface HTTP/WebSocket
- `5718`: Session Manager ZeroMQ RPC
- `6718`: Session Manager ZeroMQ PUB
- `7718`: Session Manager ZeroMQ SUB
- `6000`: Modhost Bridge ZeroMQ
- `5555`: mod-host TCP (command)
- `5556`: mod-host TCP (feedback)

### Development Setup

### Prerequisites
```bash
# System dependencies
sudo apt-get install python3 python3-pip libzmq3-dev libjack-jackd2-dev pipewire-jack

# Python dependencies (if you run the API locally instead of in Docker)
pip3 install fastapi uvicorn pyzmq asyncio
```

### Start Development Environment
```bash
# Start all services
./scripts/start-service.sh

# Development Docker helpers
# - The client API dev image is built from `client-interface/web_api/api/Dockerfile` and
#   installs Python requirements at build time. The dev compose file `docker/docker-compose.dev.yml`
#   builds the image and bind-mounts the `web_client` directory so code edits are visible without
#   rebuilding the image.

# - The session manager dev image is built from `session-manager/Dockerfile` and installs its
#   requirements at build time. The dev compose includes a `session-manager` service that bind-mounts
#   the `session-manager` directory into `/app` and runs with `network_mode: host` so ZeroMQ sockets
#   bind to localhost and other services can connect directly. Use `scripts/start-session-manager-dev.sh`
#   to stop any locally-running session manager and start the container.

# Services will log to:
# - logs/mod-host.log
# - logs/modhost-bridge.log
# - logs/session-manager.log

# Access web interface
# Open browser to http://localhost:8080

### Dev: use host networking (recommended for local development)

When developing locally it's often easiest to run the Client Interface (adapter)
container with host networking so the container can reach services bound to
127.0.0.1 on the host (for example the `session-manager` ZeroMQ RPC port).
This avoids container loopback networking issues during iterative development.

Example (run the prebuilt dev image with host networking):
```bash
# Run with host networking so adapter can connect to host-local ZeroMQ services
docker rm -f marlise-client-api-dev || true
docker run -d --name marlise-client-api-dev --network host \
    -v $(pwd)/client-interface/web_client:/app \
    --workdir /app \
    marlise-client-api-dev:latest /usr/local/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --app-dir /app
```

If you prefer not to use host networking, set the `CLIENT_INTERFACE_ZMQ_HOST`
environment variable so the adapter can reach the host ZeroMQ services. For
example `-e CLIENT_INTERFACE_ZMQ_HOST=host.docker.internal` or
`-e CLIENT_INTERFACE_ZMQ_HOST=<host-ip>`.

Using Docker Compose (dev convenience):
```yaml
services:
    client-api:
        image: marlise-client-api-dev:latest
        network_mode: host # dev convenience only; not for production
        volumes:
            - ./client-interface/web_client:/app
        working_dir: /app
        command: /usr/local/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --app-dir /app
```

## Build & Rerun (quick reference)

1. Build and run the v2 web client (development)
```bash
# from repository root
cd client-interface/web_client_v2
npm install
# start dev server with Vite (HMR)
npm run dev -- --host --port 5173
```

2. Build production bundle
```bash
cd client-interface/web_client_v2
npm install
npm run build
# serve the dist/ folder with a static server or copy to your HTTP server
```

3. Restart the client interface adapter (FastAPI) if needed
```bash
cd client-interface/web_api/api
pip3 install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

4. Health checks
```bash
curl http://localhost:8080/health
curl http://localhost:5173/
```

```

### Stop Services
```bash
./scripts/stop-service.sh
```

## Testing

### Test ZeroMQ Communication
```bash
python3 tests/test_zmq_communication.py
```

### Test HTTP API
```bash
python3 tests/test_http_api.py
```

### Test API Completeness
```bash
python3 tests/test_api_completeness.py
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8080/health

# Get available plugins
curl http://localhost:8080/api/plugins/available

# Load a plugin
curl -X POST http://localhost:8080/api/plugins \
  -H "Content-Type: application/json" \
  -d '{"uri": "http://calf.sourceforge.net/plugins/Reverb"}'

# Update parameter
curl -X PATCH http://localhost:8080/api/plugins/parameters \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "1", "port": "gain", "value": 0.5}'
```

### WebSocket Testing
```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8080/ws
```

### Development static-site and tests

- A development nginx/static-site image and a `docker/docker-compose.dev.yml` are provided to serve the web client during development and to proxy API/WebSocket calls. See `docker/README.md` for usage and examples of the `WAIT_FOR_TARGETS` environment variable that makes nginx wait for dependent services before starting.
- A smoke test `tests/test_static_site_smoke.py` is included; it brings up the `static-site` service via the dev compose file, checks that it serves HTTP, and tears it down. The test is skipped when `docker` is not available.

## Code Style and Conventions

### Python Code
- Follow **PEP 8** style guide
- Use **type hints** for function parameters and return values
- Use **async/await** for asynchronous code
- Use **docstrings** for modules, classes, and functions
- Prefer **f-strings** for string formatting

Example:
```python
async def load_plugin(self, uri: str) -> Dict[str, Any]:
    """
    Load an LV2 plugin.
    
    Args:
        uri: LV2 plugin URI
        
    Returns:
        Dict with 'success' and 'instance_id' keys
    """
    result = await self.zmq_client.call(
        "session_manager",
        "load_plugin",
        uri=uri
    )
    return result
```

### Shell Scripts
- Use `#!/bin/bash` shebang
- Set `set -e` to exit on errors for critical scripts
- Use meaningful variable names in UPPERCASE
- Add comments for non-obvious operations

### C++ Code (for modhost-bridge)
- Follow **C++11/14** standards
- Use **RAII** for resource management
- Handle errors explicitly
- Use `const` where appropriate

## Common Development Tasks

### Adding a New API Endpoint

1. **Define endpoint in Client Interface** (FastAPI)
   ```python
   @app.post("/api/new-feature")
   async def new_feature(data: NewFeatureRequest):
       result = await zmq_client.call("session_manager", "new_feature", **data.dict())
       return result
   ```

2. **Implement handler in Session Manager**
   ```python
   async def handle_new_feature(self, params: dict) -> dict:
       # Business logic here
       result = await self.bridge_client.call("new_feature", params)
       return result
   ```

3. **Update documentation** in `docs/COMMUNICATION_ARCHITECTURE.md`

## Comprehensive Testing Platform

### 4-Layer Test Architecture

Marlise includes a complete Docker-based integration test platform that tests all system layers:

```
Level 4: Client API HTTP Tests (End-to-End)
    ↕ HTTP/WebSocket  
Level 3: Session Manager ZMQ Tests (IPC Layer)
    ↕ ZeroMQ RPC
Level 2: Session Manager Direct Tests (Business Logic)
    ↕ Direct calls
Level 1: Mod-Host Bridge Direct Tests (Audio Engine)
    ↕ ZeroMQ JSON-RPC
```

### Hybrid Testing Platform (RECOMMENDED)

**✅ FULLY OPERATIONAL** - The hybrid testing approach combines reliable mock audio services with real business logic components for optimal development workflow:

```bash
cd tests
./test_hybrid_services.sh    # Hybrid platform: Mock audio + Real session manager + Real client interface
```

**Hybrid Architecture Benefits**:
- 🚀 **Fast & Reliable**: Mock audio services eliminate compilation complexity
- 🎯 **Real Business Logic**: Authentic session manager and client interface behavior  
- 🐳 **Docker-based**: Complete isolation with Ubuntu 22.04 + JACK dummy + LV2 plugins
- ⚡ **Quick Iteration**: No mod-host compilation, instant test execution
- 🔍 **Real Communication**: Actual ZeroMQ and HTTP communication patterns
- 📊 **Complete Coverage**: Plugin management, parameter control, system monitoring

**What's Hybrid**:
- ✅ **Mock mod-host**: Python TCP server simulating plugin host protocol
- ✅ **Mock modhost-bridge**: Python ZeroMQ server simulating JSON-RPC bridge
- ✅ **REAL session-manager**: Actual Python business logic service
- ✅ **REAL client-interface**: Actual FastAPI HTTP/WebSocket service

### Running Tests

#### Quick Setup Verification
```bash
cd tests
./setup_verification.sh    # Verify test platform setup
./health_check.sh          # Quick environment check
```

#### Hybrid Testing (Recommended)
```bash
cd tests
./test_hybrid_services.sh   # Full hybrid integration testing
```

#### Complete Test Suite
```bash
cd tests
./run_integration_tests.sh    # Run all 4 levels
```

#### Level-Specific Testing
```bash
cd tests
./run_integration_tests.sh --level1    # Mod-host bridge only
./run_integration_tests.sh --level2    # Session manager direct  
./run_integration_tests.sh --level3    # Session manager ZMQ
./run_integration_tests.sh --level4    # Client API HTTP
```

#### Using Make Targets
```bash
cd tests
make health-check    # Environment verification
make test           # Complete test suite
make test-level4    # HTTP API tests only
make build          # Build test images
make clean          # Clean up test environment
```

### Hybrid Testing Platform Details

**🎯 Purpose**: Optimal balance between testing coverage and development speed

**📁 Key Files**:
- `tests/test_hybrid_services.sh` - Main hybrid test orchestrator (✅ OPERATIONAL)
- `tests/docker/mock_mod_host.py` - Mock TCP audio host (✅ PROVEN)
- `tests/docker/mock_modhost_bridge.py` - Mock ZeroMQ bridge (✅ PROVEN)
- `tests/docker/docker-compose.hybrid.yml` - Hybrid Docker composition (auto-generated)
- `tests/docker/Dockerfile.hybrid-services` - Hybrid environment builder (auto-generated)

**🔧 Technical Implementation**:
- **Build Time**: ~4 minutes (227.9s) for complete environment
- **Ubuntu 22.04** base with complete audio development stack
- **JACK dummy backend** for headless audio simulation
- **LV2 plugins**: Calf, SWH, TAP plugins pre-installed
- **Supervisor process management** for service orchestration
- **Python 3.10** with FastAPI, pyzmq, pytest, and all dependencies

**🏗️ Hybrid Architecture**:
```
Web Client Tests (HTTP/WebSocket)
      ↕ 
Real FastAPI Client Interface (Port 8080)
      ↕ ZeroMQ RPC
Real Python Session Manager (Business Logic)
      ↕ ZeroMQ JSON-RPC  
Mock Modhost Bridge (Python ZMQ server)
      ↕ TCP Protocol
Mock mod-host (Python TCP server)
```

**✅ Validated Capabilities**:
- Plugin loading/removal with real session manager logic
- Parameter updates through complete communication chain
- WebSocket real-time notifications 
- ZeroMQ inter-process communication
- HTTP REST API endpoint testing
- JACK audio port simulation
- System monitoring and diagnostics
- Error handling and edge cases

**🚀 Usage Workflow**:
1. Run `./test_hybrid_services.sh`
2. Docker builds Ubuntu environment with all dependencies
3. Services start with supervisor management
4. Test suite validates full communication chain
5. Mock services provide predictable audio backend
6. Real services ensure authentic business logic behavior

### Test Environment Features

- **Docker-based isolation** - No external dependencies needed
- **JACK dummy backend** - No real audio hardware required
- **Known LV2 plugins** - Calf, SWH, TAP plugins for consistent testing
- **Complete Marlise stack** - All services running in containers
- **Supervisor management** - Automatic service restart and monitoring
- **Real-time testing** - WebSocket and ZeroMQ communication validation
- **Hybrid approach** - Mock audio + real business logic for optimal development

### Test Coverage

- ✅ **Plugin management**: Load/remove/configure across all layers
- ✅ **Parameter control**: Real-time updates and validation  
- ✅ **Audio connections**: JACK port management and routing
- ✅ **System monitoring**: CPU, memory, disk, network statistics
- ✅ **Session persistence**: Snapshots and configuration management
- ✅ **Web interface**: REST API and WebSocket communication
- ✅ **Error handling**: Invalid inputs and edge cases
- ✅ **Performance**: Concurrent access and load testing

### Adding New Tests

1. **Choose appropriate test level** based on what you're testing
2. **Add test methods** to existing test classes in `tests/integration/`
3. **Use provided fixtures** for each test level:
   - `modhost_bridge_client` (Level 1)
   - `session_manager_direct_client` (Level 2)  
   - `session_manager_zmq_client` (Level 3)
   - `client_api_client` (Level 4)
4. **Follow async test patterns** with proper cleanup
5. **Update test documentation** if adding new test categories

### Debugging Tests

- **Service logs**: Available in `tests/logs/` directory
- **Test results**: Saved in `tests/test-results/` 
- **Interactive debugging**: `docker compose exec marlise-test-env bash`
- **Show logs on failure**: `./run_integration_tests.sh --show-logs`

## Handler Implementation Status

### Comprehensive Coverage Achieved

Marlise now includes **complete handler implementation** with 68/69 handlers fully implemented (98.6% coverage):

**📊 System Handlers (39/44 implemented):**
- ✅ **System monitoring**: CPU, memory, disk, network usage with psutil + fallbacks
- ✅ **File operations**: Secure upload/download/list/delete with Base64 encoding
- ✅ **Package management**: pip and dpkg integration with security checks
- ✅ **Authentication**: Session-based login/logout/user_info via session_manager
- ✅ **Snapshot system**: Complete save/load/rename/remove/list functionality
- ✅ **Log management**: Multi-type log handling (system + application logs)
- ✅ **Configuration**: Get/set/reset config management
- ✅ **Session controls**: Reset, buffer size, xrun management
- ✅ **Hardware controls**: Shutdown, reboot, system info, truebypass, CPU frequency
- ✅ **Parameter addressing**: Plugin parameter to hardware/MIDI mapping

**🔊 JACK Handlers (25/25 implemented):**
- ✅ **All JACK operations** forwarded to bridge_client maintaining architectural consistency
- ✅ **Port management**: Connect/disconnect/list audio/MIDI/CV ports
- ✅ **Transport control**: Play/stop/pause transport states
- ✅ **Performance monitoring**: Latency, xruns, DSP load tracking
- ✅ **Advanced features**: Freewheel, timebase, repl synchronization

**❌ Deliberately Excluded:**
- `ping_hmi` - Hardware-specific HMI communication (not relevant for current setup)

### Handler Architecture

- **Consistent patterns**: All handlers follow established architectural patterns
- **Service delegation**: JACK → bridge_client, Auth → session_manager, System → direct calls
- **Robust fallbacks**: psutil with subprocess/proc fallbacks for system monitoring
- **Security-first**: Path validation, sanitized inputs, privilege separation
- **Error handling**: Comprehensive try/catch blocks with detailed logging
- **Type safety**: Proper type hints and validation throughout

### Debugging

#### Check Service Logs
```bash
tail -f logs/mod-host.log
tail -f logs/modhost-bridge.log
tail -f logs/session-manager.log
```

#### Health Check Chain
```bash
# Test full chain
curl http://localhost:8080/api/session/health

# Test session manager directly
python3 tests/test_zmq_communication.py

# Test mod-host directly
telnet localhost 5555
# Type: ping (send the text `ping` over the socket and expect a pong/ack response)
```

#### Common Issues
1. **Port conflicts**: Check if ports are in use with `netstat -tuln | grep <port>`
2. **ZeroMQ timeouts**: Services may not be started or reachable
3. **JACK not running**: Ensure JACK or PipeWire is running
4. **Plugin paths**: Check LV2_PATH environment variable

## Documentation

- **README.md**: High-level project overview and quick start
- **STRUCTURE.md**: Quick navigation guide for the repository structure
- **docs/ARCHITECTURE_OVERVIEW.md**: Comprehensive system architecture overview
- **docs/COMMUNICATION_ARCHITECTURE.md**: Complete technical documentation of all communication layers
- **docs/COMMUNICATION_QUICK_REFERENCE.md**: Quick reference for common commands and APIs
- **docs/COMMUNICATION_FLOW_DIAGRAMS.md**: Visual sequence diagrams
- **docs/MIGRATION_GUIDE.md**: Guide for migrating from old submodule structure

When adding features, update relevant documentation files.

## Git Workflow

### Branch Naming
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates
- `refactor/*`: Code refactoring

### Commit Messages
Follow conventional commits format:
```
<type>: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat: add plugin preset management endpoint
fix: resolve ZeroMQ timeout in session manager
docs: update communication architecture diagrams
```

## Important Notes

### Project Structure
- The project uses an **integrated structure** (no git submodules)
- All code is directly in the repository for easier development
- See `STRUCTURE.md` for quick navigation
- Component-specific documentation is in each component's README.md

### Audio System
- The system requires JACK or PipeWire audio server
- Use `pw-jack` wrapper when using PipeWire (default behavior)
- LV2 plugins must be installed and in the LV2_PATH

### Performance
- ZeroMQ provides microsecond-level messaging latency
- Real-time audio processing happens in mod-host (separate process)
- WebSocket provides real-time updates to browser clients

### Security
- Currently **localhost-only** communication (no authentication)
- For remote access, use VPN or SSH tunneling
- Input validation at each layer (Client Interface, Session Manager, Modhost Bridge)

## License

This project is licensed under **GNU Affero General Public License v3 (AGPL-3.0)**.

When contributing:
- Ensure your code is compatible with AGPL-3.0
- Add copyright headers to new files if required
- Respect the original MOD-UI attribution

## Getting Help

1. Check existing documentation in `docs/` directory
2. Review `STRUCTURE.md` for quick navigation
3. Review test scripts in `tests/` for usage examples
4. Examine service logs in `logs/` directory
5. Refer to [MOD-UI wiki](https://wiki.modaudio.com/) for LV2 plugin information

## Best Practices for Copilot

When working with this repository:

1. **Understand the structure**: Review `STRUCTURE.md` and `docs/ARCHITECTURE_OVERVIEW.md` before making changes
2. **Follow the 4-layer model**: Web Client → Client Interface → Session Manager → Modhost Bridge → mod-host
3. **Test incrementally**: Use the test scripts in `tests/` after making changes
4. **Check service logs**: Always verify services are running and communicating (logs in `logs/` directory)
5. **Update documentation**: Keep `docs/` files in sync with code changes
6. **Respect the modularity**: Each component folder (`audio-engine/`, `session-manager/`, `client-interface/`) has a specific responsibility
7. **Use existing patterns**: Look at similar endpoints/handlers for consistency
8. **Test the full chain**: Changes may affect multiple layers - test end-to-end
9. **Check component READMEs**: Each major component has its own README.md with specific details

## Integration test helpers (note for Copilot)

- Tests now provide a session-scoped fixture `modhost_container` which starts a single detached runtime container for the whole pytest session. Helpers are in `tests/integration/docker_helpers.py` and include:
    - `start_runtime_container(tag)` — starts a runtime container with `JACK_DUMMY=1`, discovers host ports for `5555` and `5556`, and waits for mod-host readiness.
    - `stop_container(container_id)` — forcibly removes the container.
    - `run_container_with_modhost(tag, stage)` — runs `/opt/marlise/bin/mod-host -V` inside the image (ephemeral smoke check).

When adding or changing integration tests, prefer using `modhost_container` for socket-based tests to avoid starting/stopping containers per test. Use `run_container_with_modhost` for quick exec-style binary/version checks.
