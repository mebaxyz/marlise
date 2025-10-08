# Session Manager API Reference

This document provides a comprehensive reference for all RPC methods exposed by the Session Manager service via ZeroMQ.

## Overview

The Session Manager exposes methods through ZeroMQ RPC calls. All methods follow the pattern:

```python
result = await zmq_client.call("session_manager", "method_name", **parameters)
```

## Method Categories

### Plugin Management

#### `load_plugin`

Load an LV2 plugin instance.

**Parameters:**
- `uri` (str): LV2 plugin URI
- `x` (float, optional): X position (default: 0.0)
- `y` (float, optional): Y position (default: 0.0)
- `parameters` (dict, optional): Initial parameter values

**Returns:**
```json
{
  "instance_id": "plugin_123",
  "plugin": {
    "uri": "http://example.com/plugin",
    "name": "Example Plugin",
    "parameters": {...},
    "ports": {...}
  }
}
```

**Errors:**
- Plugin not found
- Bridge communication failure
- Invalid parameters

#### `unload_plugin`

Unload a plugin instance.

**Parameters:**
- `instance_id` (str): Plugin instance ID

**Returns:**
```json
{
  "status": "ok",
  "instance_id": "plugin_123"
}
```

#### `get_plugin_info`

Get information about a loaded plugin.

**Parameters:**
- `instance_id` (str): Plugin instance ID

**Returns:**
```json
{
  "plugin": {
    "uri": "...",
    "name": "...",
    "parameters": {...},
    "ports": {...}
  }
}
```

#### `set_parameter`

Set a plugin parameter value.

**Parameters:**
- `instance_id` (str): Plugin instance ID
- `port` or `parameter` (str): Parameter name
- `value` (float): Parameter value

**Returns:**
```json
{
  "status": "ok",
  "value": 0.5
}
```

#### `get_parameter`

Get a plugin parameter value.

**Parameters:**
- `instance_id` (str): Plugin instance ID
- `parameter` (str): Parameter name

**Returns:**
```json
{
  "parameter": "gain",
  "value": 0.5
}
```

#### `get_available_plugins`

Get list of available LV2 plugins.

**Returns:**
```json
{
  "plugins": {
    "http://example.com/plugin": {
      "name": "Example Plugin",
      "brand": "Example Corp",
      "version": "1.0.0"
    }
  }
}
```

#### `list_instances`

List all loaded plugin instances.

**Returns:**
```json
{
  "instances": {
    "plugin_123": {...},
    "plugin_456": {...}
  }
}
```

### Pedalboard Management

#### `create_pedalboard`

Create a new pedalboard.

**Parameters:**
- `name` (str): Pedalboard name
- `description` (str, optional): Description

**Returns:**
```json
{
  "name": "My Pedalboard",
  "id": "pedalboard_123",
  "plugins": [],
  "connections": []
}
```

#### `load_pedalboard`

Load a pedalboard from configuration.

**Parameters:**
- `pedalboard_data` (dict): Pedalboard configuration

**Returns:**
```json
{
  "name": "Loaded Pedalboard",
  "plugins": [...],
  "connections": [...]
}
```

#### `save_pedalboard`

Save current pedalboard state.

**Returns:**
```json
{
  "status": "ok",
  "path": "/path/to/pedalboard.json"
}
```

#### `get_current_pedalboard`

Get current pedalboard state.

**Parameters:**
- `persist` (bool, optional): Whether to save to disk (default: true)

**Returns:**
```json
{
  "name": "Current Pedalboard",
  "plugins": [...],
  "connections": [...],
  "snapshots": [...]
}
```

### Connection Management

#### `create_connection`

Create an audio connection between plugins.

**Parameters:**
- `source_plugin` (str): Source plugin instance ID
- `source_port` (str): Source port name
- `target_plugin` (str): Target plugin instance ID
- `target_port` (str): Target port name

**Returns:**
```json
{
  "status": "ok",
  "connection_id": "conn_123"
}
```

#### `remove_connection`

Remove an audio connection.

**Parameters:**
- `connection_id` (str): Connection ID to remove

**Returns:**
```json
{
  "status": "ok",
  "connection_id": "conn_123"
}
```

### Snapshot Management

#### `create_snapshot`

Create a snapshot of current pedalboard state.

**Parameters:**
- `name` (str): Snapshot name

**Returns:**
```json
{
  "name": "My Snapshot",
  "timestamp": "2024-01-01T12:00:00Z",
  "plugins": [...],
  "connections": [...]
}
```

#### `apply_snapshot`

Apply a snapshot to current pedalboard.

**Parameters:**
- `snapshot` (dict): Snapshot data

**Returns:**
```json
{
  "status": "ok",
  "snapshot_name": "My Snapshot"
}
```

### Audio System Management

#### `init_jack`

Initialize JACK audio system.

**Returns:**
```json
{
  "status": "ok",
  "sample_rate": 44100,
  "buffer_size": 1024
}
```

#### `close_jack`

Close JACK audio system.

**Returns:**
```json
{
  "status": "ok"
}
```

#### `get_jack_data`

Get JACK system information.

**Returns:**
```json
{
  "sample_rate": 44100,
  "buffer_size": 1024,
  "hardware_ports": [...]
}
```

#### `set_jack_buffer_size`

Set JACK buffer size.

**Parameters:**
- `buffer_size` (int): Buffer size in frames

**Returns:**
```json
{
  "status": "ok",
  "buffer_size": 1024
}
```

#### `get_jack_sample_rate`

Get current JACK sample rate.

**Returns:**
```json
{
  "sample_rate": 44100
}
```

### Monitoring and Diagnostics

#### `health_check`

Perform service health check.

**Returns:**
```json
{
  "status": "healthy",
  "service": "session_manager",
  "version": "1.0.0"
}
```

#### `get_cpu_load`

Get current CPU load.

**Returns:**
```json
{
  "cpu_load": 45.2
}
```

#### `get_max_cpu_load`

Get maximum CPU load.

**Returns:**
```json
{
  "max_cpu_load": 78.5
}
```

#### `get_audio_levels`

Get current audio levels.

**Returns:**
```json
{
  "input_levels": [0.1, 0.2],
  "output_levels": [0.3, 0.4]
}
```

### Preset Management

#### `load_preset`

Load a plugin preset.

**Parameters:**
- `instance_id` (str): Plugin instance ID
- `preset_uri` (str): Preset URI

**Returns:**
```json
{
  "status": "ok",
  "preset_uri": "preset://example"
}
```

#### `save_preset`

Save current plugin state as preset.

**Parameters:**
- `instance_id` (str): Plugin instance ID
- `preset_name` (str): Preset name

**Returns:**
```json
{
  "status": "ok",
  "preset_uri": "preset://saved_preset"
}
```

#### `show_presets`

List available presets for a plugin.

**Parameters:**
- `instance_id` (str): Plugin instance ID

**Returns:**
```json
{
  "presets": [
    {
      "uri": "preset://preset1",
      "name": "Preset 1"
    }
  ]
}
```

### Utility Methods

#### `echo`

Echo back the input parameters (for testing).

**Parameters:**
- Any parameters

**Returns:**
```json
{
  "echo": {...}
}
```

## Error Handling

All methods return error responses in the format:

```json
{
  "success": false,
  "error": "Error description",
  "details": {...}
}
```

### Common Error Codes

- `INVALID_PARAMETERS`: Missing or invalid parameters
- `PLUGIN_NOT_FOUND`: Plugin URI not available
- `INSTANCE_NOT_FOUND`: Plugin instance doesn't exist
- `CONNECTION_FAILED`: Audio connection creation failed
- `BRIDGE_ERROR`: Communication with modhost-bridge failed
- `TIMEOUT`: Operation timed out

## Events

The service publishes events via ZeroMQ PUB socket:

### Plugin Events

- `plugin_loaded`: Plugin instance created
- `plugin_unloaded`: Plugin instance removed
- `parameter_changed`: Parameter value changed

### Connection Events

- `connection_created`: Audio connection established
- `connection_removed`: Audio connection removed

### Pedalboard Events

- `pedalboard_changed`: Pedalboard state modified
- `snapshot_created`: New snapshot saved
- `snapshot_applied`: Snapshot loaded

## Protocol Details

### Request Format

```json
{
  "service": "session_manager",
  "method": "method_name",
  "params": {...}
}
```

### Response Format

```json
{
  "success": true,
  "result": {...}
}
```

### Timeout

Default timeout: 30 seconds
Configurable via environment: `ZMQ_REQUEST_TIMEOUT`

## Examples

### Load and Configure Plugin

```python
# Load plugin
result = await zmq_client.call("session_manager", "load_plugin",
                              uri="http://calf.sourceforge.net/plugins/Reverb")
instance_id = result["instance_id"]

# Set parameter
await zmq_client.call("session_manager", "set_parameter",
                     instance_id=instance_id,
                     parameter="decay",
                     value=0.8)
```

### Create Pedalboard with Connections

```python
# Create pedalboard
pedalboard = await zmq_client.call("session_manager", "create_pedalboard",
                                  name="My Chain")

# Load plugins
reverb = await zmq_client.call("session_manager", "load_plugin",
                              uri="http://calf.sourceforge.net/plugins/Reverb")
delay = await zmq_client.call("session_manager", "load_plugin",
                             uri="http://calf.sourceforge.net/plugins/Reverb")

# Connect plugins
await zmq_client.call("session_manager", "create_connection",
                     source_plugin=reverb["instance_id"],
                     source_port="out_l",
                     target_plugin=delay["instance_id"],
                     target_port="in_l")
```