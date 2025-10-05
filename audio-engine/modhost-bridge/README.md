# Mod-Host Bridge Service (C++)

This service translates the legacy mod-host socket protocol into a JSON based ZeroMQ API. It acts as a bridge between the text-based mod-host protocol and modern JSON-based microservices.

## Architecture

The service consists of five main components:
- **Feedback Reader**: Connects to mod-host's feedback port and publishes events as JSON
- **Command Service**: Receives JSON commands via ZeroMQ and forwards them to mod-host
- **Plugin Manager**: High-level plugin management with instance tracking and parameter control
- **Audio System Manager**: JACK audio server management and port connection control
- **Health Monitor**: Provides health check endpoint for monitoring service status

## Features

- **ZeroMQ Integration**: Uses REP sockets for commands and health checks, PUB socket for feedback
- **Plugin Management**: Load, unload, and control LV2 plugin instances with parameter management
- **Audio System Management**: Complete JACK audio server control (initialization, buffer settings, port connections)
- **Event Publishing**: Publishes plugin lifecycle events (loaded, unloaded, parameter changes)
- **Health Monitoring**: Tracks connection status with automatic recovery
- **Connection Waiting**: Service waits for mod-host availability at startup
- **Thread-Safe**: Uses shared state with proper synchronization
- **Comprehensive Logging**: Detailed logging with spdlog
- **Configuration**: Environment variable based configuration

## Dependencies

- **ZeroMQ**: Messaging library
- **jsoncpp**: JSON serialization
- **spdlog**: Logging library
- **fmt**: Formatting library (required by spdlog)
- **CMake**: Build system

## Building

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get install libzmq3-dev libjsoncpp-dev libspdlog-dev libfmt-dev cmake build-essential

# Create build directory
mkdir build
cd build

# Configure and build
cmake ..
make

# Install (optional)
sudo make install
```

## Configuration

Configure the service using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOD_HOST_HOST` | `localhost` | mod-host hostname |
| `MOD_HOST_PORT` | `5555` | mod-host command port |
| `MOD_HOST_FEEDBACK_PORT` | `5556` | mod-host feedback port |
| `MODHOST_BRIDGE_REP` | `tcp://127.0.0.1:6000` | ZeroMQ REP endpoint for commands |
| `MODHOST_BRIDGE_PUB` | `tcp://127.0.0.1:6001` | ZeroMQ PUB endpoint for feedback |
| `MODHOST_BRIDGE_HEALTH` | `tcp://127.0.0.1:6002` | ZeroMQ REP endpoint for health checks |

## Usage

```bash
# Start the service
./modhost-bridge

# Or with custom configuration
MOD_HOST_HOST=192.168.1.100 MODHOST_BRIDGE_REP=tcp://0.0.0.0:6000 ./modhost-bridge
```

## Testing

A test script is provided to verify the plugin manager functionality:

```bash
# Install Python ZeroMQ binding
pip3 install pyzmq

# Run the test (requires mod-host-bridge to be running)
python3 test_plugin_manager.py
```

The test script exercises all plugin manager API endpoints and verifies correct operation.

## API

### Command Interface

Send JSON commands to the REP socket (`tcp://127.0.0.1:6000`):

**Raw command:**
```json
{"command": "add urn:lv2:plugin 123"}
```

**Structured command:**
```json
{"name": "add", "args": ["urn:lv2:plugin", "123"]}
```

**Response:**
```json
{"status": "resp 0", "raw": "resp 0"}
```

### Plugin Manager API

The plugin manager provides high-level LV2 plugin management. Send plugin commands to the REP socket (`tcp://127.0.0.1:6000`):

**Load Plugin:**
```json
{
  "action": "plugin",
  "method": "load_plugin",
  "uri": "http://guitarix.sourceforge.net/plugins/gx_distortion",
  "x": 100.0,
  "y": 200.0,
  "parameters": {
    "drive": 0.7
  }
}
```

**Unload Plugin:**
```json
{
  "action": "plugin",
  "method": "unload_plugin",
  "instance_id": "plugin_0_abc123"
}
```

**Set Parameter:**
```json
{
  "action": "plugin",
  "method": "set_parameter",
  "instance_id": "plugin_0_abc123",
  "parameter": "drive",
  "value": 0.8
}
```

**Get Parameter:**
```json
{
  "action": "plugin",
  "method": "get_parameter",
  "instance_id": "plugin_0_abc123",
  "parameter": "drive"
}
```

**Get Plugin Info:**
```json
{
  "action": "plugin",
  "method": "get_plugin_info",
  "instance_id": "plugin_0_abc123"
}
```

**List Instances:**
```json
{
  "action": "plugin",
  "method": "list_instances"
}
```

**Clear All Plugins:**
```json
{
  "action": "plugin",
  "method": "clear_all"
}
```

### Audio System API

The audio system provides JACK audio server management. Send audio commands to the REP socket (`tcp://127.0.0.1:6000`):

**Initialize JACK:**
```json
{
  "action": "audio",
  "method": "init_jack"
}
```

**Close JACK:**
```json
{
  "action": "audio",
  "method": "close_jack"
}
```

**Get JACK Data:**
```json
{
  "action": "audio",
  "method": "get_jack_data",
  "with_transport": true
}
```

**Get Buffer Size:**
```json
{
  "action": "audio",
  "method": "get_jack_buffer_size"
}
```

**Set Buffer Size:**
```json
{
  "action": "audio",
  "method": "set_jack_buffer_size",
  "size": 1024
}
```

**Get Sample Rate:**
```json
{
  "action": "audio",
  "method": "get_jack_sample_rate"
}
```

**Get Port Alias:**
```json
{
  "action": "audio",
  "method": "get_jack_port_alias",
  "port_name": "system:capture_1"
}
```

**Get Hardware Ports:**
```json
{
  "action": "audio",
  "method": "get_jack_hardware_ports",
  "is_audio": true,
  "is_output": false
}
```

**Check MIDI Features:**
```json
{
  "action": "audio",
  "method": "has_midi_beat_clock_sender_port"
}
```

**Connect Ports:**
```json
{
  "action": "audio",
  "method": "connect_jack_ports",
  "port1": "system:capture_1",
  "port2": "effect:input"
}
```

**Disconnect Ports:**
```json
{
  "action": "audio",
  "method": "disconnect_jack_ports",
  "port1": "system:capture_1",
  "port2": "effect:input"
}
```

**Reset Xruns:**
```json
{
  "action": "audio",
  "method": "reset_xruns"
}
```

### Feedback Events

Subscribe to feedback events from the PUB socket (`tcp://127.0.0.1:6001`):

**Plugin Events:**
```json
{"type": "plugin_loaded", "data": {"instance_id": "plugin_0_abc123", "uri": "http://guitarix.sourceforge.net/plugins/gx_distortion", "name": "GX Distortion"}}
{"type": "plugin_unloaded", "data": {"instance_id": "plugin_0_abc123", "uri": "http://guitarix.sourceforge.net/plugins/gx_distortion"}}
{"type": "parameter_changed", "data": {"instance_id": "plugin_0_abc123", "parameter": "drive", "value": 0.8}}
```

**mod-host Feedback:**
```json
{"type": "param_set", "effect_id": 1, "symbol": "volume", "value": 0.8}
{"type": "audio_monitor", "index": 0, "value": 0.5}
{"type": "log", "level": 1, "message": "Plugin loaded"}
```

### Health Check

Query service health via the health REP socket (`tcp://127.0.0.1:6002`):

**Request:**
```json
{"action": "health"}
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is healthy, all connections established",
  "command_connected": true,
  "feedback_connected": true
}
```

## Health States

- **starting**: Service initializing, waiting for connections
- **healthy**: Both command and feedback connections established
- **degraded**: Command connection available, feedback connection lost
- **unhealthy**: Cannot connect to mod-host

## Development

### Project Structure

```
modhost-bridge/
├── CMakeLists.txt          # Build configuration
├── README.md              # This file
├── src/                   # Source and header files
│   ├── main.cpp           # Main application
│   ├── types.h            # Data structures and types
│   ├── types.cpp          # Type implementations
│   ├── parser.h           # Feedback message parser
│   ├── parser.cpp         # Parser implementation
│   ├── feedback_reader.h  # Feedback reader class
│   ├── feedback_reader.cpp # Feedback reader implementation
│   ├── command_service.h  # Command service class
│   ├── command_service.cpp # Command service implementation
│   ├── plugin_manager.h   # Plugin manager class
│   ├── plugin_manager.cpp # Plugin manager implementation
│   ├── health_monitor.h   # Health monitor class
│   └── health_monitor.cpp # Health monitor implementation
```

### Building for Development

```bash
# Debug build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# Release build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

## License

See LICENSE file in the project root.


## Note about auto-build / auto-start behavior

Auto-build and auto-start behavior for `mod-host` has been removed from this project. The bridge no longer attempts to build or spawn the `mod-host` process. Please start `mod-host` separately (for example via your orchestration, container, or a developer script) and ensure the JACK/pipewire audio server is available before starting the bridge. The bridge will wait for `mod-host` to be reachable on the configured ports before enabling services.
Please note: auto-build and auto-start of `mod-host` was removed from this repository. Start `mod-host` separately and ensure JACK/pipewire is available before launching the bridge.