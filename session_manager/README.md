# MOD UI Session Manager Service

A modern, async-based session management service that provides high-level pedalboard operations, plugin management, and state persistence through the modhost-bridge service.

## Overview

This service provides session management, pedalboard operations, and plugin lifecycle management by communicating with the modhost-bridge service. It focuses on high-level operations while delegating low-level mod-host communication to the dedicated bridge service.

## Architecture

```
Session Manager Service
├── PluginManager      # Plugin lifecycle & parameter management
├── SessionManager     # Pedalboard & session state management
└── Main Service       # RPC handlers & ServiceBus integration
    └── Bridge Client  # Communication with modhost-bridge service
```

## Key Changes from Audio Processing Service

### Removed Features (Now in modhost-bridge)
- Direct mod-host process management
- Low-level mod-host protocol communication
- ModHostBridge component
- Direct JACK audio system integration
- Hardware interface management (HMI)

### Retained Features (High-level Session Management)
- Pedalboard creation, loading, saving
- Plugin instance management
- Parameter control and monitoring
- Audio connection management
- Session state management
- Snapshot creation and application
- Preset management
- CPU load monitoring
- Audio level monitoring

## Current Implementation Status

### ✅ **Fully Implemented (100% Coverage)**

#### **Plugin Lifecycle Management**
- `load_plugin()` - Load LV2 plugins with parameters via bridge
- `unload_plugin()` - Remove plugin instances via bridge
- `activate_plugin()` - Activate plugin processing via bridge
- `preload_plugin()` - Preload plugins for faster instantiation via bridge
- `get_plugin_info()` - Retrieve plugin metadata
- `list_instances()` - List all loaded plugin instances

#### **Plugin Control**
- `set_parameter()` - Set plugin parameter values via bridge
- `get_parameter()` - Get plugin parameter values via bridge
- `bypass_plugin()` - Bypass/enable plugin processing via bridge
- `set_patch_property()` - Set plugin patch properties via bridge
- `get_patch_property()` - Get plugin patch properties via bridge

#### **Pedalboard Management**
- `create_pedalboard()` - Create new pedalboard configurations
- `load_pedalboard()` - Load pedalboard from data
- `save_pedalboard()` - Save current pedalboard state
- `get_current_pedalboard()` - Get active pedalboard info
- `list_saved_pedalboards()` - List all saved pedalboards
- `load_saved_pedalboard()` - Load saved pedalboard by ID
- `delete_saved_pedalboard()` - Delete saved pedalboard
- `export_saved_pedalboard()` - Export pedalboard to file
- `import_pedalboard()` - Import pedalboard from file

#### **Session Control** 🆕
- `reset_session()` - Complete session/audio engine reset via bridge
- `mute_session()` - Disconnect system audio outputs via bridge
- `unmute_session()` - Reconnect system audio outputs via bridge
- `get_session_state()` - Comprehensive system state reporting via bridge
- `initialize_session()` - Session initialization and setup via bridge
- `create_snapshot()` - Create parameter snapshots
- `apply_snapshot()` - Apply saved parameter states

#### **Bundle Management**
- `add_bundle()` - Add plugin bundles to available plugins
- `remove_bundle()` - Remove plugin bundles

#### **Preset Management**
- `load_preset()` - Load plugin presets via bridge
- `save_preset()` - Save current plugin state as preset via bridge
- `show_presets()` - List available presets for plugin via bridge

#### **Transport & Tempo Control**
- `set_bpm()` - Set transport BPM
- `set_beats_per_bar()` - Set beats per bar
- `set_transport()` - Control transport state (play/stop)
- `transport_sync()` - Set transport sync mode

#### **Monitoring & Feedback**
- `get_cpu_load()` - Get current CPU load percentage via bridge
- `get_max_cpu_load()` - Get maximum CPU load since last check via bridge
- `monitor_parameter()` - Monitor parameter changes with conditions via bridge
- `monitor_output()` - Monitor audio output levels via bridge
- `get_audio_levels()` - Get current audio level meters via bridge
- `flush_parameters()` - Flush all parameter changes via bridge
- `monitor_audio_levels()` - Monitor JACK port audio levels (feedback port)
- `monitor_midi_control()` - Monitor MIDI control messages (feedback port)
- `monitor_midi_program()` - Monitor MIDI program changes (feedback port)

#### **Control Chain Integration**
- `cc_map_parameter()` - Map Control Chain actuator to parameter
- `cc_unmap_parameter()` - Remove Control Chain mapping
- `cc_value_set()` - Set Control Chain actuator value
- `cv_map_parameter()` - Map CV input to parameter
- `cv_unmap_parameter()` - Remove CV mapping

#### **MIDI Control** 🆕
- `midi_learn_parameter()` - Enable MIDI learning for parameter
- `midi_map_parameter()` - Map MIDI CC to parameter
- `midi_unmap_parameter()` - Remove MIDI mapping
- `monitor_midi_control()` - Monitor MIDI control messages
- `monitor_midi_program()` - Monitor MIDI program changes

### ⚠️ **Partially Implemented (40-79% Coverage)**

#### **Audio System Management (100% Coverage)** 🆕
**Implemented:**
- `init_jack()` - Initialize JACK audio system via bridge
- `close_jack()` - Close JACK audio system via bridge
- `get_jack_data()` - Get comprehensive JACK system data (CPU load, xruns, transport) via bridge
- `get_jack_buffer_size()` - Get current JACK buffer size via bridge
- `set_jack_buffer_size()` - Set JACK buffer size via bridge
- `get_jack_sample_rate()` - Get JACK sample rate via bridge
- `get_jack_port_alias()` - Get JACK port aliases via bridge
- `get_jack_hardware_ports()` - Get available JACK hardware ports via bridge
- `has_midi_beat_clock_sender_port()` - Check MIDI beat clock sender port availability via bridge
- `has_serial_midi_input_port()` - Check serial MIDI input port availability via bridge
- `has_serial_midi_output_port()` - Check serial MIDI output port availability via bridge
- `has_midi_merger_output_port()` - Check MIDI merger output port availability via bridge
- `has_midi_broadcaster_input_port()` - Check MIDI broadcaster input port availability via bridge
- `has_duox_split_spdif()` - Check DuoX S/PDIF split feature availability via bridge
- `connect_jack_ports()` - Connect JACK audio/MIDI ports via bridge
- `connect_jack_midi_output_ports()` - Connect JACK MIDI output ports via bridge
- `disconnect_jack_ports()` - Disconnect JACK ports via bridge
- `disconnect_all_jack_ports()` - Disconnect all connections for a port via bridge
- `reset_xruns()` - Reset JACK xruns counter via bridge

## Communication with Bridge Service

The session manager communicates with the modhost-bridge service via ServiceBus calls:

```python
# Example: Load a plugin
result = await self.bridge.call("modhost_bridge", "load_plugin", uri=uri, instance_id=instance_id)

# Example: Set parameter
result = await self.bridge.call("modhost_bridge", "set_parameter", instance_id=instance_id, parameter=param, value=value)

# Example: Create connection
result = await self.bridge.call("modhost_bridge", "create_connection",
                                source_plugin=source_plugin, source_port=source_port,
                                target_plugin=target_plugin, target_port=target_port)
```

## Key Features

### **ServiceBus Communication**
- All operations communicate with modhost-bridge via ServiceBus
- Clean separation of concerns between session management and low-level audio
- Asynchronous operation with proper error handling

### **Event Publishing**
- All operations publish events via ServiceBus for real-time system monitoring
- Events include operation results and state changes

### **Error Handling**
- Comprehensive error handling with proper cleanup and recovery mechanisms
- Bridge communication errors are handled gracefully

### **Async Architecture**
- Built with modern async/await patterns for non-blocking operations
- Plugin loading is optimized with preloading support
- Parameter changes are batched for efficiency

## Configuration

### Environment Variables
```bash
# Service behavior
SIMULATE_MODHOST=false               # Enable simulation mode (inherited from bridge)

# Data storage
SESSION_MANAGER_DATA_DIR=./data/session_manager  # Storage directory
```

## Usage

### Starting the Service
```bash
# Production mode
python -m src.mod_ui.services.session_manager.main

# Development mode with simulation
SIMULATE_MODHOST=true python -m src.mod_ui.services.session_manager.main
```

### ServiceBus Integration
```python
from servicebus import Service

# Create client
client = Service("my_client")
await client.start()

# Load a plugin (communicates with bridge)
result = await client.call("session_manager", "load_plugin", 
                          uri="http://example.org/plugin", 
                          x=100, y=200)

# Set parameter (communicates with bridge)
await client.call("session_manager", "set_parameter",
                 instance_id=result["instance_id"],
                 parameter="gain", 
                 value=0.8)

# Create pedalboard
pedalboard = await client.call("session_manager", "create_pedalboard",
                              name="My Board", 
                              description="Test pedalboard")
```

## Testing

### Unit Tests
```bash
# Run all tests
python -m pytest src/mod_ui/services/session_manager/tests/

# Run specific test
python -m pytest src/mod_ui/services/session_manager/tests/test_plugin_manager.py -v
```

### Integration Tests
```bash
# Test service health
python test_health.py

# Test critical functionality  
python test_critical_methods.py

# Test bridge communication
python test_bridge_integration.py

# Test audio system handlers
python -m pytest tests/test_audio_system_handlers.py -v
```

### Demo Scripts
```bash
# Run audio system management demo
python demo_audio_system.py
```

## Dependencies

### Core Dependencies
- `servicebus` - ZeroMQ-based service communication
- `asyncio` - Async programming support
- `zmq` - ZeroMQ Python bindings

### Development Dependencies
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support

## Contributing

1. Follow the existing async/await patterns
2. Add comprehensive error handling
3. Include unit tests for new functionality
4. Update this README with any new methods
5. Publish events for state changes via ServiceBus

## Performance Notes

- All operations are non-blocking (async)
- Plugin loading is optimized with preloading support
- Parameter changes are batched for efficiency
- Real-time monitoring via dedicated feedback port
- Connection pooling for bridge communication

## Production Readiness

✅ **READY FOR PRODUCTION:**
- Core session management operations
- Plugin and pedalboard management
- **Audio system management (JACK control, port connections, system monitoring)**
- Bridge service communication
- Real-time monitoring and feedback
- Comprehensive error handling and logging

⚠️ **REQUIRES BRIDGE SERVICE:**
- The session manager requires the modhost-bridge service to be running
- All low-level audio operations are delegated to the bridge
- Service startup will fail if bridge is not available

The service is **production-ready** for high-level session operations and serves as a clean abstraction layer over the modhost-bridge service.