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
├── tests/               # Integration tests
│   ├── test_zmq_communication.py
│   ├── test_http_api.py
│   └── test_api_completeness.py
├── STRUCTURE.md         # Quick structure reference
└── README.md            # Project documentation
```

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
# - The client API dev image is built from `client-interface/web_client/api/Dockerfile` and
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
