# Marlise Architecture Overview

This document provides a comprehensive overview of the Marlise architecture and how the components work together.

## Design Philosophy

Marlise follows a layered architecture with clear separation of concerns:

1. **Audio Engine** - Low-level, real-time audio processing
2. **Session Manager** - High-level orchestration and state management
3. **Client Interface** - User-facing API and web interface

Each layer has a well-defined responsibility and communicates through standardized protocols.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                             │
│                   (User Interface)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/WebSocket
                        │ (JSON)
┌───────────────────────▼─────────────────────────────────────┐
│                 Client Interface                             │
│                    (FastAPI)                                 │
│  • REST API endpoints                                        │
│  • WebSocket for real-time events                           │
│  • Static file serving                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ ZeroMQ
                        │ (JSON-RPC + PubSub)
┌───────────────────────▼─────────────────────────────────────┐
│                 Session Manager                              │
│                    (Python)                                  │
│  • Plugin lifecycle management                               │
│  • Pedalboard state management                               │
│  • Connection orchestration                                  │
│  • State persistence                                         │
└───────────────────────┬─────────────────────────────────────┘
                        │ ZeroMQ
                        │ (JSON-RPC)
┌───────────────────────▼─────────────────────────────────────┐
│                 Modhost Bridge                               │
│                    (C++)                                     │
│  • JSON-RPC to text protocol translation                     │
│  • Command validation                                        │
│  • Response parsing                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ TCP Socket
                        │ (Text commands)
┌───────────────────────▼─────────────────────────────────────┐
│                    mod-host                                  │
│                  (LV2 Plugin Host)                           │
│  • LV2 plugin loading and management                         │
│  • JACK audio processing                                     │
│  • Real-time audio connections                               │
└─────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
marlise/
├── audio-engine/              # Audio Engine Layer
│   ├── mod-host/              # LV2 plugin host binary
│   │   ├── src/               # mod-host source code (if building)
│   │   └── mod-host           # Compiled binary
│   └── modhost-bridge/        # JSON-RPC bridge service
│       ├── build/             # Build output
│       └── modhost-bridge     # Compiled binary
│
├── session-manager/           # Session Manager Layer
│   ├── src/                   # Python source code
│   │   ├── session_manager.py # Main service
│   │   ├── pedalboard.py      # Pedalboard management
│   │   ├── plugin_manager.py  # Plugin operations
│   │   └── zmq_client.py      # ZeroMQ communication
│   └── start_session_manager.sh
│
├── client-interface/          # Client Interface Layer
│   ├── api/                   # FastAPI backend
│   │   ├── main.py            # FastAPI application
│   │   ├── routes/            # API route handlers
│   │   ├── websocket.py       # WebSocket handler
│   │   └── zmq_client.py      # ZeroMQ communication
│   └── web/                   # Web client (static files)
│       ├── index.html
│       ├── css/
│       └── js/
│
├── scripts/                   # Utility scripts
│   ├── start-service.sh       # Start all services
│   ├── stop-service.sh        # Stop all services
│   └── README.md
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE_OVERVIEW.md        # This file
│   ├── COMMUNICATION_ARCHITECTURE.md   # Protocol details
│   ├── COMMUNICATION_QUICK_REFERENCE.md
│   └── COMMUNICATION_FLOW_DIAGRAMS.md
│
├── tests/                     # Integration tests
│   ├── test_zmq_communication.py
│   ├── test_http_api.py
│   └── test_api_completeness.py
│
├── logs/                      # Runtime logs (gitignored)
├── run/                       # PID files (gitignored)
├── build/                     # Build artifacts (gitignored)
├── .gitignore
├── LICENSE
└── README.md
```

## Communication Protocols

### Layer 1: Web Client ↔ Client Interface
- **Protocol**: HTTP/HTTPS and WebSocket
- **Port**: 8080 (configurable)
- **Data Format**: JSON
- **Use Cases**: 
  - REST API calls for CRUD operations
  - Real-time event streaming via WebSocket

### Layer 2: Client Interface ↔ Session Manager
- **Protocol**: ZeroMQ (REQ/REP + PUB/SUB)
- **Ports**: 5718 (RPC), 6718 (PUB), 7718 (SUB)
- **Data Format**: JSON-RPC 2.0
- **Use Cases**:
  - RPC for synchronous operations
  - PubSub for event broadcasting

### Layer 3: Session Manager ↔ Modhost Bridge
- **Protocol**: ZeroMQ (REQ/REP)
- **Port**: 6000
- **Data Format**: JSON-RPC 2.0
- **Use Cases**:
  - Plugin operations
  - Audio connection management
  - System queries

### Layer 4: Modhost Bridge ↔ mod-host
- **Protocol**: TCP Socket
- **Port**: 5555
- **Data Format**: Plain text commands
- **Use Cases**:
  - Low-level plugin commands
  - JACK audio operations

## Data Flow Examples

### Loading a Plugin

1. **User Action**: Clicks "Add Plugin" in web UI
2. **HTTP Request**: `POST /api/plugins` with plugin URI
3. **Client Interface**: Validates request
4. **ZMQ RPC Call**: Client → Session Manager (`load_plugin`)
5. **Session Manager**: 
   - Allocates instance ID
   - Stores plugin in session state
6. **ZMQ RPC Call**: Session Manager → Modhost Bridge (`load_plugin`)
7. **Modhost Bridge**: Translates to text command
8. **TCP Command**: `add <URI> <instance_id>`
9. **mod-host**: Loads LV2 plugin, returns success
10. **Response Chain**: Success propagates back through all layers
11. **WebSocket Event**: `plugin_loaded` event broadcast to all clients

### Parameter Update

1. **User Action**: Adjusts knob in web UI
2. **HTTP Request**: `PATCH /api/plugins/parameters`
3. **Client Interface → Session Manager**: `set_parameter` RPC
4. **Session Manager**: Updates internal state
5. **Session Manager → Modhost Bridge**: `set_parameter` RPC
6. **Modhost Bridge → mod-host**: `param_set <instance> <port> <value>`
7. **mod-host**: Updates plugin parameter in real-time
8. **WebSocket Event**: `parameter_changed` broadcast to clients

## Key Benefits of This Architecture

### ✅ Separation of Concerns
- Each layer has a single, well-defined responsibility
- Changes in one layer don't affect others
- Easy to test components independently

### ✅ Language-Appropriate Implementation
- C for real-time audio processing (mod-host)
- C++ for efficient protocol bridging (modhost-bridge)
- Python for high-level logic and web services (session-manager, client-interface)

### ✅ Scalability
- ZeroMQ provides high-performance messaging
- Stateless REST API allows horizontal scaling
- PubSub pattern efficiently handles multiple clients

### ✅ Maintainability
- Clear folder structure mirrors architectural layers
- Self-documenting component names
- Standardized communication protocols

### ✅ Flexibility
- Components can be replaced independently
- Easy to add new client types (mobile app, CLI, etc.)
- Protocol abstraction allows backend changes

## Development Workflow

### Running the System

1. **Start Audio Engine**:
```bash
./scripts/start-service.sh
```
This starts mod-host, waits for it to be ready, then starts modhost-bridge and session-manager.

2. **Start Client Interface** (separately):
```bash
cd client-interface
python -m api.main
```

3. **Access Web UI**:
```
http://localhost:8080
```

### Testing

Run integration tests:
```bash
python tests/test_zmq_communication.py
python tests/test_http_api.py
```

### Stopping Services

```bash
./scripts/stop-service.sh
```

## Configuration

All components use environment variables for configuration:

### Audio Engine
- `MOD_HOST_PORT=5555` - mod-host command port
- `MOD_HOST_FEEDBACK_PORT=5556` - mod-host feedback port
- `USE_PWJACK=1` - Use PipeWire JACK wrapper

### Session Manager
- `BRIDGE_CONNECT_RETRIES=5` - Connection retry attempts
- `SESSION_MANAGER_AUTO_CREATE_DEFAULT=1` - Auto-create default pedalboard

### Client Interface
- `CLIENT_INTERFACE_PORT=8080` - HTTP server port

## Further Reading

- [Communication Architecture](COMMUNICATION_ARCHITECTURE.md) - Detailed protocol specifications
- [Quick Reference](COMMUNICATION_QUICK_REFERENCE.md) - API endpoint summary
- [Flow Diagrams](COMMUNICATION_FLOW_DIAGRAMS.md) - Visual sequence diagrams
- Component READMEs in each directory
