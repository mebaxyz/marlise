# API Documentation: /api/session/state

## Overview
This endpoint provides the current session state information needed for rendering the MOD UI templates. It replaces the direct dependency on the local `host.py` module.

## HTTP Request
```
GET /api/session/state
```

## Response Format
```json
{
  "pedalboard_name": "My Pedalboard",
  "snapshot_name": "Clean Tone",
  "pedalboard_path": "/home/user/.pedalboards/My Pedalboard.pedalboard",
  "pedalboard_size": {
    "width": 800,
    "height": 600
  },
  "hardware_profile": [
    {
      "actuator": "footswitch",
      "type": "momentary",
      "label": "FS1",
      "color": "#ff0000"
    }
  ]
}
```

## Field Descriptions

### Required Fields
- **`pedalboard_name`** (string): The name of the currently loaded pedalboard. Empty string if no pedalboard is loaded.
- **`snapshot_name`** (string): The name of the currently active snapshot. Empty string if no snapshot is active.
- **`pedalboard_path`** (string): The filesystem path to the currently loaded pedalboard bundle. Empty string if no pedalboard is loaded.
- **`pedalboard_size`** (object): The dimensions of the pedalboard canvas.
  - `width` (number): Canvas width in pixels
  - `height` (number): Canvas height in pixels
- **`hardware_profile`** (array): Array of hardware actuator configurations for the current device.

### Optional Fields
All fields are technically optional as the webserver provides fallback defaults.

## Usage in Templates

The data from this endpoint is used to populate the following template variables in `index.html`:

- `title`: The pedalboard name (used for page title)
- `bundlepath`: The pedalboard bundle path
- `size`: JSON-encoded pedalboard size object
- `fulltitle`: Combined pedalboard name + snapshot name (e.g., "My Pedalboard - Clean Tone")
- `titleblend`: CSS class based on whether pedalboard name exists
- `hardware_profile`: Base64-encoded JSON array of hardware actuators

## Fallback Behavior

If the API call fails or returns incomplete data, the webserver uses these defaults:
- `pedalboard_name`: `""` (empty string)
- `snapshot_name`: `""` (empty string)  
- `pedalboard_path`: `""` (empty string)
- `pedalboard_size`: `{"width": 800, "height": 600}`
- `hardware_profile`: `[]` (empty array)

## Implementation Notes

- This endpoint should return data for the **currently active session** only
- The response should be fast (< 100ms) as it's called on every page load
- Hardware profile should match the current device's actuator configuration
- Pedalboard size should reflect the actual canvas dimensions used in the UI

## Example Backend Implementation

```python
@app.get("/api/session/state")
async def get_session_state():
    # Get current session data from your backend state management
    current_session = get_current_session()
    
    return {
        "pedalboard_name": current_session.pedalboard_name or "",
        "snapshot_name": current_session.snapshot_name or "",
        "pedalboard_path": current_session.pedalboard_path or "",
        "pedalboard_size": {
            "width": current_session.canvas_width,
            "height": current_session.canvas_height
        },
        "hardware_profile": current_session.hardware_actuators
    }
```</content>
<parameter name="filePath">/home/nicolas/project/marlise/client-interface/web_client_original/API_SESSION_STATE.md