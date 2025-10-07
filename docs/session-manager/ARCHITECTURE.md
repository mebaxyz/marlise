# Session Manager Architecture

This document describes the internal architecture of the Session Manager service, including component relationships, data flow, and design decisions.

## High-Level Architecture

The Session Manager is built around several key principles:

- **Async-First**: All operations are asynchronous using Python's `asyncio`
- **Service-Oriented**: Clear separation between plugin management, session coordination, and communication
- **Event-Driven**: Pub/sub events for real-time updates
- **Error-Resilient**: Graceful degradation and comprehensive error handling

## Component Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │────│ Client Interface │────│ Session Manager │
│   (Browser)     │    │   (FastAPI)      │    │   (Python)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Modhost Bridge  │────│ Bridge Client    │────│ Plugin Manager  │
│   (C++)         │    │   (ZeroMQ)       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   mod-host      │────│ Session Control  │────│ Connection      │
│ (LV2 Host)      │    │   Service        │    │ Service         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ Pedalboard      │
                                               │ Service         │
                                               └─────────────────┘
```

## Core Components

### 1. Main Service (`main.py`)

**Responsibilities:**
- Service lifecycle management (startup/shutdown)
- Component initialization and wiring
- Signal handling for graceful shutdown
- Global state management

**Key Features:**
- Uses module-level globals for simple runtime wiring
- Supports restart during testing
- Environment-based configuration
- Retry logic for bridge connection

### 2. Plugin Manager (`core/plugin_manager.py`)

**Responsibilities:**
- LV2 plugin discovery and loading
- Parameter management and validation
- Plugin instance lifecycle
- Event publishing for plugin changes

**Key Features:**
- Thread-safe operations with asyncio.Lock
- Parameter validation against plugin metadata
- Event-driven updates via ZeroMQ pub/sub
- Comprehensive error handling

**Data Structures:**
```python
@dataclass
class PluginInstance:
    uri: str
    instance_id: str
    name: str
    brand: str
    version: str
    parameters: Dict[str, Any]
    ports: Dict[str, Any]
    available_parameters: Dict[str, Any]
    x: float
    y: float
    enabled: bool
    preset: Optional[str]
    created_at: str
```

### 3. Session Manager (`core/session_manager.py`)

**Responsibilities:**
- High-level session coordination
- Delegation to specialized services
- Session-level locking for consistency

**Delegated Services:**
- **Pedalboard Service**: Pedalboard lifecycle and persistence
- **Connection Service**: Audio connection management
- **Session Control Service**: Audio system operations

### 4. Bridge Client (`core/bridge_client.py`)

**Responsibilities:**
- ZeroMQ communication with modhost-bridge
- Protocol translation (JSON-RPC to bridge format)
- Connection management and error handling

**Protocol Mapping:**
- Audio commands: `{"action": "audio", "method": "..."}`
- Plugin commands: `{"action": "plugin", "method": "..."}`
- Direct commands for connections: `connect/disconnect` text commands

### 5. ZMQ Service (`zmq_service.py`)

**Responsibilities:**
- ZeroMQ socket management (RPC, PUB, SUB)
- Dynamic port assignment based on service name
- Handler registration and dispatch
- Event publishing and subscription

**Socket Types:**
- **REP (RPC)**: Handles incoming method calls
- **PUB**: Publishes events to subscribers
- **SUB**: Receives events from other services
- **REQ**: Makes calls to other services

### 6. ZMQ Handlers (`handlers/zmq_handlers.py`)

**Responsibilities:**
- RPC method implementation
- Parameter validation and error handling
- Delegation to appropriate services
- Response formatting

**Handler Categories:**
- Plugin management (load, unload, parameters)
- Pedalboard operations (create, load, save)
- Connection management
- Audio system control
- Monitoring and diagnostics

## Data Flow

### Plugin Loading Sequence

1. Client calls `load_plugin` via ZeroMQ RPC
2. Handler validates parameters and calls PluginManager.load_plugin()
3. PluginManager queries available plugins from bridge
4. Bridge client sends `load_plugin` to modhost-bridge
5. Bridge returns instance_id, PluginManager verifies registration
6. PluginManager creates PluginInstance and stores it
7. Event published via ZeroMQ PUB socket
8. Success response returned to client

### Pedalboard Operations

1. Client requests pedalboard operation
2. SessionManager acquires lock and delegates to PedalboardService
3. PedalboardService coordinates with PluginManager and ConnectionService
4. State changes published as events
5. Updated state persisted if requested

## Error Handling

### Strategy

- **Fail Fast**: Critical startup errors prevent service start
- **Graceful Degradation**: Non-critical errors logged but don't stop operations
- **Comprehensive Logging**: All errors logged with context
- **Client-Friendly**: Error responses include actionable information

### Error Types

- **Connection Errors**: Bridge communication failures
- **Validation Errors**: Invalid parameters or state
- **Resource Errors**: Plugin loading failures, disk I/O issues
- **Timeout Errors**: Bridge response timeouts

## Configuration Management

### Environment Variables

Used for runtime configuration without code changes:

- Service endpoints and timeouts
- Retry policies and delays
- Feature flags (auto-create pedalboard)
- Debug and logging levels

### Dynamic Configuration

Some settings can be changed at runtime via API calls:
- JACK buffer size
- Audio system parameters
- Plugin parameters

## Event System

### Event Types

- `plugin_loaded`: New plugin instance created
- `plugin_unloaded`: Plugin instance removed
- `parameter_changed`: Plugin parameter updated
- `connection_created`: Audio connection established
- `connection_removed`: Audio connection removed
- `pedalboard_changed`: Pedalboard state modified

### Publishing

Events are published via ZeroMQ PUB socket with JSON payloads:
```json
{
  "event": "plugin_loaded",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "instance_id": "plugin_123",
    "uri": "http://example.com/plugin",
    "name": "Example Plugin"
  }
}
```

## Testing and Development

### Unit Testing

Each component has focused unit tests:
- Mock external dependencies (bridge, ZMQ)
- Test error conditions and edge cases
- Validate event publishing

### Integration Testing

End-to-end tests verify component interaction:
- Full plugin loading workflow
- Pedalboard save/load cycles
- Connection management
- Event propagation

### Development Tools

- Async-first design enables easy testing
- Module-level globals support test isolation
- Comprehensive logging aids debugging
- Environment-based configuration simplifies testing

## Performance Considerations

### Async Design

- All I/O operations are asynchronous
- ZeroMQ provides low-latency communication
- Event-driven architecture minimizes polling

### Resource Management

- Connection pooling for ZeroMQ sockets
- Lazy initialization of expensive resources
- Proper cleanup in shutdown sequences

### Scalability

- Stateless design allows horizontal scaling
- Event-driven updates reduce client polling
- Efficient JSON serialization for network communication

## Future Enhancements

### Planned Improvements

- Plugin preset management
- Advanced routing algorithms
- Real-time parameter monitoring
- Distributed session management

### Extensibility

The modular architecture supports adding new services:
- Custom plugin types
- Alternative audio backends
- Advanced DSP processing
- Machine learning integration