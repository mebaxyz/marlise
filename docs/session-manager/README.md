# Session Manager Documentation

The Session Manager is a high-level service in the Marlise audio processing system that coordinates pedalboard sessions, plugin management, and state persistence. It acts as the central orchestrator between the web client interface, the modhost-bridge (C++ service), and the underlying mod-host LV2 plugin host.

## Overview

The Session Manager provides a comprehensive API for managing audio processing sessions, including:

- **Plugin Management**: Loading, unloading, and configuring LV2 audio plugins
- **Pedalboard Management**: Creating, loading, saving, and managing pedalboard configurations
- **Connection Management**: Creating and managing audio connections between plugins
- **Snapshot Management**: Saving and restoring pedalboard states
- **Session Control**: Audio system initialization, JACK integration, and session-wide operations

## Architecture

The Session Manager follows a layered architecture with clear separation of concerns:

```
Web Client Interface (FastAPI)
    ↓ HTTP/WebSocket
Client Interface (FastAPI)
    ↓ ZeroMQ RPC + PubSub
Session Manager (Python asyncio)
    ↓ ZeroMQ JSON-RPC
Modhost Bridge (C++ service)
    ↓ TCP Text Protocol
mod-host (LV2 Plugin Host)
```

### Core Components

1. **Main Service (`main.py`)**: Entry point that initializes all components and manages the service lifecycle
2. **Plugin Manager (`core/plugin_manager.py`)**: Handles plugin loading, unloading, and parameter control
3. **Session Manager (`core/session_manager.py`)**: Main coordinator delegating to specialized services
4. **Bridge Client (`core/bridge_client.py`)**: ZeroMQ client for communicating with modhost-bridge
5. **ZMQ Service (`zmq_service.py`)**: ZeroMQ RPC and pub/sub implementation
6. **ZMQ Handlers (`handlers/zmq_handlers.py`)**: RPC method handlers for incoming requests

### Specialized Services

The Session Manager delegates to several specialized services:

- **Pedalboard Service**: Handles pedalboard lifecycle and persistence
- **Connection Service**: Manages audio connections between plugins
- **Session Control Service**: Handles session-level audio operations

## Quick Start

### Prerequisites

- Python 3.8+
- ZeroMQ libraries
- JACK Audio Connection Kit or PipeWire
- LV2 plugin packages

### Installation

```bash
cd session-manager
pip install -r requirements.txt
```

### Running the Service

```bash
python -m session-manager.main
```

The service will:
1. Start ZeroMQ RPC and pub/sub services
2. Connect to the modhost-bridge service
3. Initialize plugin and session management
4. Begin accepting RPC calls

### Health Check

```bash
# Via ZeroMQ (using zmq-cli or similar)
# Or via the client interface health endpoint
curl http://localhost:8080/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODHOST_BRIDGE_ENDPOINT` | `tcp://127.0.0.1:6000` | Bridge service endpoint |
| `MODHOST_BRIDGE_TIMEOUT` | `5.0` | Bridge call timeout in seconds |
| `BRIDGE_CONNECT_RETRIES` | `5` | Number of bridge connection retries |
| `BRIDGE_CONNECT_RETRY_DELAY` | `1.0` | Delay between connection retries |
| `SESSION_MANAGER_AUTO_CREATE_DEFAULT` | `0` | Auto-create default pedalboard on startup |

### Ports

The service uses dynamically assigned ports based on service name hash:

- RPC: Base port + hash (default ~5718)
- PUB: RPC port + 1000 (~6718)
- SUB: RPC port + 2000 (~7718)

## API Reference

See [API_REFERENCE.md](API_REFERENCE.md) for detailed method documentation.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development setup and testing.

## Troubleshooting

### Common Issues

1. **Bridge Connection Failed**
   - Ensure modhost-bridge service is running
   - Check ZeroMQ endpoint configuration
   - Verify firewall allows local connections

2. **Plugin Loading Errors**
   - Verify LV2_PATH environment variable
   - Check plugin URI format
   - Ensure JACK/PipeWire is running

3. **Audio System Issues**
   - Verify JACK or PipeWire installation
   - Check audio hardware configuration
   - Monitor JACK logs for connection issues

### Logs

Service logs are written to:
- `logs/session-manager.log`
- `logs/modhost-bridge.log`
- `logs/mod-host.log`

### Debugging

Enable debug logging:
```bash
export PYTHONPATH=/path/to/session-manager
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## Related Documentation

- [Project Architecture](../../docs/ARCHITECTURE_OVERVIEW.md)
- [Communication Architecture](../../docs/COMMUNICATION_ARCHITECTURE.md)
- [Client Interface Documentation](../client-interface/README.md)