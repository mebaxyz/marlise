# Modhost Bridge Message Schemas

This document describes all incoming and outgoing messages supported by the modhost-bridge service, including their JSON schemas and data structures.

## Table of Contents

1. [Commands](#commands)
   - [Raw Commands](#raw-commands)
   - [Structured Commands](#structured-commands)
   - [Plugin Commands](#plugin-commands)
   - [Audio System Commands](#audio-system-commands)
2. [Events](#events)
3. [Data Types](#data-types)

---

## Commands

Commands are request-response pairs sent via the ZeroMQ REP socket. Each command has a specific request format and returns a corresponding response.

### Raw Commands

**Purpose:** Send raw text commands directly to mod-host.

#### Message: Raw Command

#### Request
**JSON Schema:**
```json
{
  "command": "string"
}
```

**Example:**
```json
{
  "command": "add http://lv2plug.in/plugins/eg-amp 0"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "raw": "string"
}
```

### Structured Commands

**Purpose:** Send structured commands with name and arguments to mod-host.

#### Message: Structured Command

#### Request
**JSON Schema:**
```json
{
  "name": "string",
  "args": ["string", "string", ...]
}
```

**Example:**
```json
{
  "name": "add",
  "args": ["http://lv2plug.in/plugins/eg-amp", "0"]
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "raw": "string"
}
```

### Plugin Commands

**Purpose:** High-level plugin management operations.

#### Message: load_plugin

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "load_plugin",
  "uri": "string",
  "x": "number (optional, default: 0.0)",
  "y": "number (optional, default: 0.0)",
  "parameters": {
    "parameter_name": "number",
    ...
  } (optional)
}
```

#### Response
**JSON Schema:**
```json
{
  "instance_id": "string",
  "plugin": PluginInstance
}
```

#### Message: unload_plugin

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "unload_plugin",
  "instance_id": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "instance_id": "string"
}
```

#### Message: set_parameter

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "set_parameter",
  "instance_id": "string",
  "parameter": "string",
  "value": "number"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "value": "number"
}
```

#### Message: get_parameter

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_parameter",
  "instance_id": "string",
  "parameter": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "parameter": "string",
  "value": "number"
}
```

#### Message: get_plugin_info

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_plugin_info",
  "instance_id": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugin": PluginInstance
}
```

#### Message: list_instances

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "list_instances"
}
```

#### Response
**JSON Schema:**
```json
{
  "instances": {
    "instance_id": PluginInstance,
    ...
  }
}
```

#### Message: clear_all

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "clear_all"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string"
}
```

#### Message: get_available_plugins

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_available_plugins"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugins": {
    "plugin_uri": PluginInfo,
    ...
  }
}
```

#### Message: search_plugins

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "search_plugins",
  "query": "string",
  "criteria": {
    "category": "string (optional)",
    "author": "string (optional)",
    "min_audio_inputs": "integer (optional)",
    "min_audio_outputs": "integer (optional)",
    "max_audio_inputs": "integer (optional)",
    "max_audio_outputs": "integer (optional)",
    "requires_realtime": "boolean (optional)",
    "has_parameter": "string (optional)",
    "required_features": ["string", ...] (optional)
  } (optional)
}
```

#### Response
**JSON Schema:**
```json
{
  "plugins": [PluginInfo, ...]
}
```

#### Message: get_plugin_presets

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_plugin_presets",
  "plugin_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugin_uri": "string",
  "presets": [
    {
      "uri": "string",
      "label": "string",
      "path": "string"
    },
    ...
  ]
}
```

#### Message: load_preset

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "load_preset",
  "plugin_uri": "string",
  "preset_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "preset_uri": "string"
}
```

#### Message: save_preset

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "save_preset",
  "plugin_uri": "string",
  "preset": {
    "uri": "string",
    "label": "string",
    "path": "string"
  }
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "preset_uri": "string"
}
```

#### Message: rescan_plugins

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "rescan_plugins"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string",
  "plugins_added": "integer",
  "plugins_removed": "integer"
}
```

#### Message: validate_preset

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "validate_preset",
  "plugin_uri": "string",
  "preset_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "is_valid": "boolean"
}
```

#### Message: rescan_presets

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "rescan_presets",
  "plugin_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "string"
}
```

#### Message: get_plugin_gui

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_plugin_gui",
  "plugin_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugin_uri": "string",
  "gui": PluginGUI | null
}
```

#### Message: get_plugin_gui_mini

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_plugin_gui_mini",
  "plugin_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugin_uri": "string",
  "gui_mini": PluginGUI_Mini | null
}
```

#### Message: get_plugin_essentials

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "get_plugin_essentials",
  "plugin_uri": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugin_uri": "string",
  "essentials": PluginInfo_Essentials | null
}
```

#### Message: is_bundle_loaded

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "is_bundle_loaded",
  "bundle_path": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "is_loaded": "boolean"
}
```

#### Message: add_bundle

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "add_bundle",
  "bundle_path": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "added_plugins": ["string", ...]
}
```

#### Message: remove_bundle

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "remove_bundle",
  "bundle_path": "string",
  "resource_path": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "removed_plugins": ["string", ...]
}
```

#### Message: list_bundle_plugins

#### Request
**JSON Schema:**
```json
{
  "action": "plugin",
  "method": "list_bundle_plugins",
  "bundle_path": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "plugins": ["string", ...]
}
```

#### Message: health

#### Request
**JSON Schema:**
```json
{
  "action": "health"
}
```

#### Response
**JSON Schema:**
```json
{
  "status": "starting|healthy|degraded|unhealthy",
  "message": "string",
  "command_connected": "boolean",
  "feedback_connected": "boolean"
}
```

### Audio System Commands

**Purpose:** JACK audio system management operations.

#### Message: init_jack

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "init_jack"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: close_jack

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "close_jack"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: get_jack_data

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "get_jack_data",
  "with_transport": "boolean (optional, default: false)"
}
```

#### Response
**JSON Schema:**
```json
{
  "cpu_load": "number",
  "xruns": "integer",
  "rolling": "boolean",
  "bpb": "number",
  "bpm": "number"
}
```

#### Message: get_jack_buffer_size

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "get_jack_buffer_size"
}
```

#### Response
**JSON Schema:**
```json
{
  "buffer_size": "integer"
}
```

#### Message: set_jack_buffer_size

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "set_jack_buffer_size",
  "size": "integer"
}
```

#### Response
**JSON Schema:**
```json
{
  "buffer_size": "integer"
}
```

#### Message: get_jack_sample_rate

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "get_jack_sample_rate"
}
```

#### Response
**JSON Schema:**
```json
{
  "sample_rate": "number"
}
```

#### Message: get_jack_port_alias

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "get_jack_port_alias",
  "port_name": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "alias": "string"
}
```

#### Message: get_jack_hardware_ports

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "get_jack_hardware_ports",
  "is_audio": "boolean",
  "is_output": "boolean"
}
```

#### Response
**JSON Schema:**
```json
{
  "ports": ["string", ...]
}
```

#### Message: has_midi_beat_clock_sender_port

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_midi_beat_clock_sender_port"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_port": "boolean"
}
```

#### Message: has_serial_midi_input_port

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_serial_midi_input_port"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_port": "boolean"
}
```

#### Message: has_serial_midi_output_port

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_serial_midi_output_port"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_port": "boolean"
}
```

#### Message: has_midi_merger_output_port

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_midi_merger_output_port"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_port": "boolean"
}
```

#### Message: has_midi_broadcaster_input_port

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_midi_broadcaster_input_port"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_port": "boolean"
}
```

#### Message: has_duox_split_spdif

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "has_duox_split_spdif"
}
```

#### Response
**JSON Schema:**
```json
{
  "has_feature": "boolean"
}
```

#### Message: connect_jack_ports

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "connect_jack_ports",
  "port1": "string",
  "port2": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: connect_jack_midi_output_ports

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "connect_jack_midi_output_ports",
  "port": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: disconnect_jack_ports

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "disconnect_jack_ports",
  "port1": "string",
  "port2": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: disconnect_all_jack_ports

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "disconnect_all_jack_ports",
  "port": "string"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

#### Message: reset_xruns

#### Request
**JSON Schema:**
```json
{
  "action": "audio",
  "method": "reset_xruns"
}
```

#### Response
**JSON Schema:**
```json
{
  "success": "boolean"
}
```

---

## Events

Events are asynchronous messages sent via the ZeroMQ PUB socket about mod-host state changes. Clients can subscribe to these events to monitor real-time changes.

### ParamSet

**Purpose:** Parameter value changed.

**JSON Schema:**
```json
{
  "type": "param_set",
  "effect_id": "integer",
  "symbol": "string",
  "value": "number"
}
```

### AudioMonitor

**Purpose:** Audio monitoring data.

**JSON Schema:**
```json
{
  "type": "audio_monitor",
  "index": "integer",
  "value": "number"
}
```

### OutputSet

**Purpose:** Output parameter changed.

**JSON Schema:**
```json
{
  "type": "output_set",
  "effect_id": "integer",
  "symbol": "string",
  "value": "number"
}
```

### MidiMapped

**Purpose:** MIDI mapping information.

**JSON Schema:**
```json
{
  "type": "midi_mapped",
  "effect_id": "integer",
  "symbol": "string",
  "channel": "integer",
  "controller": "integer"
}
```

### MidiControlChange

**Purpose:** MIDI control change received.

**JSON Schema:**
```json
{
  "type": "midi_control_change",
  "channel": "integer",
  "control": "integer",
  "value": "integer"
}
```

### MidiProgramChange

**Purpose:** MIDI program change received.

**JSON Schema:**
```json
{
  "type": "midi_program_change",
  "program": "integer",
  "channel": "integer"
}
```

### Transport

**Purpose:** Transport state changed.

**JSON Schema:**
```json
{
  "type": "transport",
  "rolling": "boolean",
  "bpb": "number",
  "bpm": "number"
}
```

### PatchSet

**Purpose:** Patch parameter changed.

**JSON Schema:**
```json
{
  "type": "patch_set",
  "instance": "integer",
  "symbol": "string",
  "value": "any"
}
```

### Log

**Purpose:** Log message from mod-host.

**JSON Schema:**
```json
{
  "type": "log",
  "level": "integer",
  "message": "string"
}
```

### CpuLoad

**Purpose:** CPU load information.

**JSON Schema:**
```json
{
  "type": "cpu_load",
  "load": "number",
  "max_load": "number",
  "xruns": "integer"
}
```

### DataFinish

**Purpose:** Data processing finished.

**JSON Schema:**
```json
{
  "type": "data_finish"
}
```

### CcMap

**Purpose:** Control change mapping.

**JSON Schema:**
```json
{
  "type": "cc_map",
  "raw": "string"
}
```

### UnknownFeedback

**Purpose:** Unknown feedback message.

**JSON Schema:**
```json
{
  "type": "unknown",
  "raw": "string"
}
```

---

## Data Types

### PluginInfo

**Purpose:** Complete plugin metadata.

**JSON Schema:**
```json
{
  "uri": "string",
  "name": "string",
  "brand": "string",
  "label": "string",
  "comment": "string",
  "build_environment": "string",
  "version": "string",
  "license": "string",
  "category": ["string", ...],
  "author": {
    "name": "string",
    "homepage": "string",
    "email": "string"
  },
  "ports": {
    "audio_inputs": [PluginPort, ...],
    "audio_outputs": [PluginPort, ...],
    "control_inputs": [PluginPort, ...],
    "control_outputs": [PluginPort, ...],
    "cv_inputs": [PluginPort, ...],
    "cv_outputs": [PluginPort, ...],
    "midi_inputs": [PluginPort, ...],
    "midi_outputs": [PluginPort, ...]
  }
}
```

### PluginInstance

**Purpose:** Information about a loaded plugin instance.

**JSON Schema:**
```json
{
  "uri": "string",
  "instance_id": "string",
  "name": "string",
  "brand": "string",
  "version": "string",
  "x": "number",
  "y": "number",
  "enabled": "boolean",
  "preset": "string",
  "parameters": {
    "parameter_name": "number",
    ...
  },
  "ports": {
    "audio_inputs": "integer",
    "audio_outputs": "integer",
    "control_inputs": "integer",
    "control_outputs": "integer"
  },
  "created_at": "string (ISO 8601)"
}
```

### PluginGUI

**Purpose:** Complete GUI information for a plugin.

**JSON Schema:**
```json
{
  "resources_directory": "string",
  "icon_template": "string",
  "settings_template": "string",
  "javascript": "string",
  "stylesheet": "string",
  "screenshot": "string",
  "thumbnail": "string",
  "discussion_url": "string",
  "documentation": "string",
  "brand": "string",
  "label": "string",
  "model": "string",
  "panel": "string",
  "color": "string",
  "knob": "string",
  "ports": [
    {
      "valid": "boolean",
      "index": "integer",
      "name": "string",
      "symbol": "string"
    },
    ...
  ],
  "monitored_outputs": ["string", ...]
}
```

### PluginGUI_Mini

**Purpose:** Minimal GUI information for a plugin.

**JSON Schema:**
```json
{
  "resources_directory": "string",
  "screenshot": "string",
  "thumbnail": "string"
}
```

### PluginInfo_Essentials

**Purpose:** Essential plugin information.

**JSON Schema:**
```json
{
  "control_inputs": [
    {
      "index": "integer",
      "name": "string",
      "symbol": "string",
      "short_name": "string",
      "comment": "string",
      "designation": "string",
      "min_value": "number",
      "max_value": "number",
      "default_value": "number",
      "units": {
        "label": "string",
        "symbol": "string"
      },
      "properties": ["string", ...],
      "scale_points": [
        {
          "value": "number",
          "label": "string"
        },
        ...
      ]
    },
    ...
  ],
  "monitored_outputs": ["string", ...],
  "parameters": [
    {
      "valid": "boolean",
      "readable": "boolean",
      "writable": "boolean",
      "uri": "string",
      "label": "string",
      "type": "string",
      "ranges": "number|string|integer",
      "units": {
        "label": "string",
        "symbol": "string"
      },
      "comment": "string",
      "short_name": "string",
      "file_types": ["string", ...],
      "supported_extensions": ["string", ...]
    },
    ...
  ],
  "build_environment": "string",
  "micro_version": "integer",
  "minor_version": "integer",
  "release": "integer",
  "builder": "integer"
}
```

---

## Notes

- All string fields are UTF-8 encoded
- All numeric fields use JSON number type (double precision)
- Optional fields are marked as "(optional)" in the schemas
- Array fields can be empty but must be present unless marked optional
- Boolean fields use JSON true/false values
- Timestamps are in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Plugin URIs follow LV2 specification format
- Instance IDs are auto-generated unique identifiers
- Error responses include an "error" field with descriptive message</content>
<parameter name="filePath">/home/nicolas/project/madeline/mado-audio-host/modhost-bridge/MESSAGE_SCHEMAS.md