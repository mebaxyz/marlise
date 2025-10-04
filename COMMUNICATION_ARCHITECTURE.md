# MOD-UI Communication Architecture Documentation

## Overview

This document describes the complete communication architecture of the MOD-UI system, detailing how each component communicates with others through various protocols and message formats.

## System Architecture

```
┌─────────────────┐    HTTP/WebSocket    ┌──────────────────┐
│   Web Client    │ ◄─────────────────► │ Client Interface │
│   (Browser)     │                      │   (FastAPI)      │
└─────────────────┘                      └──────────────────┘
                                                   │
                                                   │ ZeroMQ
                                                   │ (RPC + PubSub)
                                                   ▼
                                         ┌──────────────────┐
                                         │ Session Manager  │
                                         │   (Python)       │
                                         └──────────────────┘
                                                   │
                                                   │ ZeroMQ
                                                   │ (JSON-RPC)
                                                   ▼
                                         ┌──────────────────┐
                                         │ Modhost Bridge   │
                                         │    (C++)         │
                                         └──────────────────┘
                                                   │
                                                   │ TCP Socket
                                                   │ (Text Protocol)
                                                   ▼
                                         ┌──────────────────┐
                                         │    mod-host      │
                                         │    (LV2 Host)    │
                                         └──────────────────┘
```

## Communication Layers

### 1. Web Client ↔ Client Interface

**Protocol:** HTTP/WebSocket  
**Port:** 8080 (configurable)  
**Data Format:** JSON  

#### HTTP REST API Endpoints

##### Plugin Management
```http
GET /api/plugins/available
Response: {"plugins": [{"uri": "...", "name": "...", "brand": "..."}]}

POST /api/plugins
Body: {"uri": "http://plugin.uri", "x": 100, "y": 200}
Response: {"success": true, "instance_id": "1"}

DELETE /api/plugins/{instance_id}
Response: {"success": true}

PATCH /api/plugins/parameters  
Body: {"instance_id": "1", "port": "gain", "value": 0.5}
Response: {"success": true}
```

##### Pedalboard Management
```http
POST /api/pedalboards
Body: {"name": "My Pedalboard", "description": "..."}
Response: {"success": true, "pedalboard": {...}}

GET /api/pedalboards/current
Response: {"success": true, "pedalboard": {...}}
```

##### Health & Status
```http
GET /health
Response: {
  "service": "client_interface",
  "status": "healthy", 
  "details": {
    "active_connections": 2,
    "zmq_client_connected": true
  }
}

GET /api/session/health
Response: {"success": true, "status": "healthy", "components": {...}}
```

#### WebSocket Communication

**Endpoint:** `ws://localhost:8080/ws`

##### Client → Server Messages
```json
{
  "event": "ping",
  "data": {},
  "timestamp": 1696435200
}
```

##### Server → Client Messages
```json
// Plugin loaded event
{
  "event": "plugin_loaded",
  "data": {
    "instance_id": "1",
    "uri": "http://plugin.uri", 
    "x": 100,
    "y": 200
  }
}

// Parameter changed event  
{
  "event": "parameter_changed",
  "data": {
    "instance_id": "1",
    "port": "gain",
    "value": 0.5
  }
}

// Plugin unloaded event
{
  "event": "plugin_unloaded", 
  "data": {
    "instance_id": "1"
  }
}
```

### 2. Client Interface ↔ Session Manager

**Protocol:** ZeroMQ (REQ/REP + PUB/SUB)  
**Ports:** Deterministic based on service name hash  
**Data Format:** JSON-RPC  

#### Port Allocation
```python
# Port calculation (from zmq_service.py)
service_hash = zlib.crc32(service_name.encode("utf-8")) % 1000
rpc_port = 5555 + service_hash        # REQ/REP for RPC calls
pub_port = 5555 + service_hash + 1000 # PUB socket for events
sub_port = 5555 + service_hash + 2000 # SUB socket for events

# Example for "session_manager":
# RPC Port: 5718, PUB Port: 6718, SUB Port: 7718
```

#### RPC Message Format

##### Request Structure
```json
{
  "method": "load_plugin",
  "params": {
    "uri": "http://plugin.uri"
  },
  "source_service": "client_interface", 
  "request_id": "uuid-here",
  "timestamp": "2025-10-04T10:30:00Z"
}
```

##### Response Structure
```json
{
  "request_id": "uuid-here",
  "result": {
    "success": true,
    "instance_id": "1"
  },
  "timestamp": "2025-10-04T10:30:01Z"
}

// Or error response:
{
  "request_id": "uuid-here", 
  "error": "Plugin not found",
  "timestamp": "2025-10-04T10:30:01Z"
}
```

#### Available RPC Methods

##### Plugin Management
```json
// Get available plugins
{"method": "get_available_plugins", "params": {}}

// Load plugin
{"method": "load_plugin", "params": {"uri": "http://plugin.uri"}}

// Unload plugin  
{"method": "unload_plugin", "params": {"instance_id": "1"}}

// Get plugin info
{"method": "get_plugin_info", "params": {"uri": "http://plugin.uri"}}

// List instances
{"method": "list_instances", "params": {}}

// Set parameter
{"method": "set_parameter", "params": {"instance_id": "1", "port": "gain", "value": 0.5}}

// Get parameter
{"method": "get_parameter", "params": {"instance_id": "1", "port": "gain"}}
```

##### Pedalboard Management
```json
// Create pedalboard
{"method": "create_pedalboard", "params": {"name": "My Board"}}

// Load pedalboard
{"method": "load_pedalboard", "params": {"data": {...}}}

// Save pedalboard
{"method": "save_pedalboard", "params": {"filename": "my-board.json"}}

// Get current pedalboard
{"method": "get_current_pedalboard", "params": {}}
```

##### Connection Management  
```json
// Create connection
{"method": "create_connection", "params": {"source": "plugin_1:out_1", "target": "plugin_2:in_1"}}

// Remove connection
{"method": "remove_connection", "params": {"source": "plugin_1:out_1", "target": "plugin_2:in_1"}}
```

##### System & Health
```json
// Health check
{"method": "health_check", "params": {}}

// Echo test
{"method": "echo", "params": {"message": "test"}}
```

#### Event Publishing (PUB/SUB)

##### Event Structure
```json
{
  "event_type": "plugin_loaded",
  "data": {
    "instance_id": "1",
    "uri": "http://plugin.uri"
  },
  "source_service": "session_manager",
  "timestamp": "2025-10-04T10:30:00Z"
}
```

##### Event Types
- `plugin_loaded` - Plugin successfully loaded
- `plugin_unloaded` - Plugin removed
- `parameter_changed` - Plugin parameter updated
- `pedalboard_created` - New pedalboard created  
- `pedalboard_loaded` - Pedalboard loaded
- `pedalboard_saved` - Pedalboard saved
- `connection_created` - Audio connection made
- `connection_removed` - Audio connection removed
- `service_started` - Service initialization complete

### 3. Session Manager ↔ Modhost Bridge

**Protocol:** ZeroMQ (REQ/REP)  
**Port:** 6000 (modhost-bridge default)  
**Data Format:** JSON-RPC  

#### Communication Flow

The session manager acts as a client, sending JSON-RPC requests to the modhost-bridge service.

#### Message Format

##### Request Structure
```json
{
  "method": "load_plugin",
  "params": {
    "uri": "http://calf.sourceforge.net/plugins/Reverb",
    "instance_id": 1
  },
  "id": 123
}
```

##### Response Structure  
```json
{
  "result": {
    "success": true,
    "instance_id": 1,
    "ports": {
      "audio": {
        "inputs": ["audio_in_1", "audio_in_2"],
        "outputs": ["audio_out_1", "audio_out_2"] 
      },
      "control": {
        "inputs": ["bypass", "dry_wet", "decay_time"]
      }
    }
  },
  "id": 123
}

// Or error response:
{
  "error": {
    "code": -1,
    "message": "Plugin not found"
  },
  "id": 123
}
```

#### Available Methods

##### Core Plugin Operations
```json
// Load plugin
{
  "method": "load_plugin",
  "params": {"uri": "http://plugin.uri", "instance_id": 1}
}

// Unload plugin
{
  "method": "unload_plugin", 
  "params": {"instance_id": 1}
}

// Set parameter value
{
  "method": "set_parameter",
  "params": {"instance_id": 1, "port": "gain", "value": 0.5}
}

// Get parameter value
{
  "method": "get_parameter",
  "params": {"instance_id": 1, "port": "gain"}
}
```

##### Plugin Information
```json
// Get available plugins
{"method": "get_available_plugins", "params": {}}

// Get plugin info
{"method": "get_plugin_info", "params": {"uri": "http://plugin.uri"}}

// Preload plugin (for faster loading)
{"method": "preload_plugin", "params": {"uri": "http://plugin.uri"}}
```

##### Audio Connections
```json  
// Connect ports
{
  "method": "connect_ports",
  "params": {"output_port": "plugin_1:out_1", "input_port": "plugin_2:in_1"}
}

// Disconnect ports
{
  "method": "disconnect_ports",
  "params": {"output_port": "plugin_1:out_1", "input_port": "plugin_2:in_1"}
}

// Disconnect all ports for an instance
{
  "method": "disconnect_all_ports", 
  "params": {"instance_id": 1}
}
```

##### System Operations
```json
// Health check
{"method": "health_check", "params": {}}

// Get CPU load
{"method": "get_cpu_load", "params": {}}

// Clear all plugins
{"method": "clear_all", "params": {}}
```

##### JACK Audio System
```json
// Initialize JACK
{"method": "init_jack", "params": {}}

// Get JACK data
{"method": "get_jack_data", "params": {"with_transport": false}}

// Get buffer size  
{"method": "get_jack_buffer_size", "params": {}}

// Set buffer size
{"method": "set_jack_buffer_size", "params": {"size": 256}}

// Get sample rate
{"method": "get_jack_sample_rate", "params": {}}

// Connect JACK ports
{"method": "connect_jack_ports", "params": {"port1": "system:capture_1", "port2": "plugin_1:in_1"}}

// Get hardware ports
{"method": "get_jack_hardware_ports", "params": {"is_audio": true, "is_output": false}}
```

### 4. Modhost Bridge ↔ mod-host  

**Protocol:** TCP Socket  
**Port:** 5555 (mod-host default)  
**Data Format:** Plain text commands  

#### Communication Flow

The modhost-bridge sends text commands to mod-host and receives text responses.

#### Command Format

Commands are sent as plain text strings terminated by newline (`\n`).

#### Core Commands

##### Plugin Management
```bash
# Add plugin  
add <plugin_uri> <instance_id>
# Example: add http://calf.sourceforge.net/plugins/Reverb 0
# Response: resp 0

# Remove plugin
remove <instance_id>  
# Example: remove 0
# Response: resp 0

# Connect ports
connect <output_port> <input_port>
# Example: connect system:capture_1 effect_0:in
# Response: resp 0

# Disconnect ports  
disconnect <output_port> <input_port>
# Example: disconnect system:capture_1 effect_0:in  
# Response: resp 0

# Set parameter
param_set <instance_id> <param_symbol> <value>
# Example: param_set 0 gain 0.5
# Response: resp 0

# Get parameter
param_get <instance_id> <param_symbol>
# Example: param_get 0 gain
# Response: resp 0.5
```

##### System Commands  
```bash
# Help (list commands)
help
# Response: List of available commands

# Quit mod-host
quit  
# Response: bye

# Get CPU load
cpu_load
# Response: resp <cpu_percentage>

# License info  
license
# Response: GPL license text
```

##### Preset Management
```bash
# Load preset
preset_load <instance_id> <preset_uri>
# Example: preset_load 0 file:///path/to/preset.lv2/preset.ttl
# Response: resp 0

# Save preset  
preset_save <instance_id> <preset_uri> <dir> <filename>
# Example: preset_save 0 http://example.com/preset /tmp mypreset
# Response: resp 0

# Show presets for plugin
preset_show <plugin_uri>
# Example: preset_show http://calf.sourceforge.net/plugins/Reverb
# Response: List of available presets
```

#### Response Codes

mod-host responds with standardized codes:

```bash
resp 0          # Success
resp -1         # Generic error  
resp -2         # Invalid URI
resp -3         # Plugin not found
resp -4         # Instance already exists
resp -5         # Instance not found
resp -6         # Port not found  
resp -7         # Connection failed
resp -101       # Invalid command
resp -102       # Invalid parameter
```

#### Error Handling

The modhost-bridge translates mod-host response codes into JSON-RPC errors:

```cpp
// C++ error translation (from modhost-bridge)
if (response.find("resp 0") == 0) {
    return success_response;
} else if (response.find("resp -3") == 0) {
    return error_response("Plugin not found", -3);
} else if (response.find("resp -5") == 0) {
    return error_response("Instance not found", -5);
}
```

## Configuration

### Environment Variables

```bash
# Client Interface
CLIENT_INTERFACE_PORT=8080

# Session Manager  
SESSION_MANAGER_AUTO_CREATE_DEFAULT=1
BRIDGE_CONNECT_RETRIES=5
BRIDGE_CONNECT_RETRY_DELAY=1.0

# Modhost Bridge
MODHOST_BRIDGE_ENDPOINT=tcp://127.0.0.1:6000
MOD_HOST_HOST=127.0.0.1
MOD_HOST_PORT=5555

# mod-host
MOD_HOST_ARGS="-n -p 5555 -f 5556 -v"
USE_PWJACK=1
```

### Port Summary

| Service | Protocol | Default Port | Purpose |
|---------|----------|--------------|---------|
| Client Interface | HTTP/WebSocket | 8080 | Web API & real-time updates |
| Session Manager | ZeroMQ REP | 5718* | RPC server |
| Session Manager | ZeroMQ PUB | 6718* | Event publishing |  
| Session Manager | ZeroMQ SUB | 7718* | Event subscription |
| Modhost Bridge | ZeroMQ REP | 6000 | JSON-RPC server |
| mod-host | TCP Socket | 5555 | Text command interface |
| mod-host | TCP Socket | 5556 | Feedback/monitoring |

*Ports calculated from service name hash

## Error Handling & Recovery

### Connection Failures

1. **Client Interface → Session Manager**
   - Timeout: 5-10 seconds per RPC call  
   - Retry: Handled at application level
   - Fallback: HTTP 503 Service Unavailable

2. **Session Manager → Modhost Bridge**  
   - Timeout: Configurable via environment
   - Retry: 5 attempts with 1s delay (configurable)
   - Fallback: Error propagated to client

3. **Modhost Bridge → mod-host**
   - Timeout: Internal C++ timeout handling
   - Retry: Automatic reconnection on disconnect  
   - Fallback: JSON-RPC error response

### Service Recovery

Services are designed to be stateless where possible:

- **Session Manager**: Maintains plugin state, can recover connections
- **Modhost Bridge**: Stateless proxy, reconnects automatically  
- **Client Interface**: Stateless web service
- **mod-host**: LV2 host maintains audio graph state

## Performance Considerations

### Message Throughput

- **ZeroMQ**: High performance, low latency (~microsecond range)
- **HTTP/WebSocket**: Moderate performance (~millisecond range)  
- **TCP Socket**: Very low overhead for simple text commands

### Audio Latency

The audio processing chain has minimal communication overhead:
- Plugin parameters: Direct memory access within mod-host
- Audio routing: JACK internal connections (sample-accurate)
- Control changes: Batched parameter updates

### Scalability  

- **Concurrent Clients**: Client Interface can handle multiple WebSocket connections
- **Plugin Load**: Limited by mod-host and available CPU/memory
- **Message Rate**: ZeroMQ can handle thousands of messages per second

## Debugging & Monitoring

### Log Locations

```bash
logs/mod-host.log          # mod-host output
logs/modhost-bridge.log    # Bridge service output  
logs/session-manager.log   # Session manager output
```

### Health Check Chain

```bash
# Test full chain
curl http://localhost:8080/api/session/health

# Test session manager directly  
python3 test_zmq_communication.py

# Test modhost bridge
# (Manual ZMQ client to port 6000)

# Test mod-host  
telnet localhost 5555
help
```

### Common Issues

1. **Port Conflicts**: Check if ports are already in use
2. **ZeroMQ Timeouts**: Increase timeout values in environment  
3. **JACK Issues**: Ensure JACK is running and accessible
4. **Plugin Loading**: Check LV2 plugin paths and permissions

## Security Considerations

### Network Security
- All communication is currently localhost-only
- No authentication/authorization implemented
- Consider VPN/SSH tunneling for remote access

### Input Validation  
- Client Interface validates JSON schemas
- Session Manager validates parameter ranges
- Modhost Bridge sanitizes text commands
- mod-host validates LV2 plugin URIs

---

This documentation covers the complete communication architecture. Each layer has specific protocols and message formats optimized for its role in the audio processing pipeline.