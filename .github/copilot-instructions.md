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
├── mod-ui/              # Submodule: MOD-UI frontend (feature/fastapi-migration branch)
├── mado-audio-host/     # Submodule: Audio host components
├── scripts/             # Service management scripts
│   ├── start-service.sh # Start all services
│   └── stop-service.sh  # Stop all services
├── test_*.py            # Test scripts
├── COMMUNICATION_*.md   # Architecture documentation
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

## Development Setup

### Prerequisites
```bash
# System dependencies
sudo apt-get install python3 python3-pip libzmq3-dev libjack-jackd2-dev pipewire-jack

# Python dependencies (if requirements.txt exists in submodules)
pip3 install fastapi uvicorn pyzmq asyncio
```

### Initialize Submodules
```bash
git submodule init
git submodule update --recursive
```

### Start Development Environment
```bash
# Start all services
./scripts/start-service.sh

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
python3 test_zmq_communication.py
```

### Test HTTP API
```bash
python3 test_http_api.py
```

### Test API Completeness
```bash
python3 test_api_completeness.py
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

3. **Update documentation** in `COMMUNICATION_ARCHITECTURE.md`

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
python3 test_zmq_communication.py

# Test mod-host directly
telnet localhost 5555
# Type: help
```

#### Common Issues
1. **Port conflicts**: Check if ports are in use with `netstat -tuln | grep <port>`
2. **ZeroMQ timeouts**: Services may not be started or reachable
3. **JACK not running**: Ensure JACK or PipeWire is running
4. **Plugin paths**: Check LV2_PATH environment variable

### Working with Submodules

```bash
# Update submodules to latest commit
git submodule update --remote

# Check submodule status
git submodule status

# Make changes in submodule
cd mod-ui
git checkout -b feature/my-feature
# ... make changes ...
git commit -am "My changes"
git push origin feature/my-feature
```

## Documentation

- **README.md**: High-level project overview and quick start
- **COMMUNICATION_ARCHITECTURE.md**: Complete technical documentation of all communication layers
- **COMMUNICATION_QUICK_REFERENCE.md**: Quick reference for common commands and APIs
- **COMMUNICATION_FLOW_DIAGRAMS.md**: Visual sequence diagrams

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

### Submodules
- **mod-ui**: Uses the `feature/fastapi-migration` branch
- **mado-audio-host**: Contains C++ modhost-bridge and mod-host binaries
- Always run `git submodule update` after pulling changes

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

1. Check existing documentation in `COMMUNICATION_*.md` files
2. Review test scripts for usage examples
3. Examine service logs in `logs/` directory
4. Refer to [MOD-UI wiki](https://wiki.modaudio.com/) for LV2 plugin information

## Best Practices for Copilot

When working with this repository:

1. **Read the architecture docs first**: Understand the 4-layer communication model before making changes
2. **Test incrementally**: Use the provided test scripts after making changes
3. **Check service logs**: Always verify services are running and communicating
4. **Follow the data flow**: Web Client → Client Interface → Session Manager → Modhost Bridge → mod-host
5. **Update documentation**: Keep `COMMUNICATION_*.md` files in sync with code changes
6. **Respect the modularity**: Each layer has a specific responsibility
7. **Use existing patterns**: Look at similar endpoints/handlers for consistency
8. **Test the full chain**: Changes may affect multiple layers - test end-to-end
