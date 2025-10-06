# Template API Endpoints Documentation

This document describes all the API endpoints needed to replace the hardcoded dependencies in the webserver templating system.

## 1. Session State Endpoint (already implemented)

### GET /api/session/state

**Purpose:** Get current session state for index.html template

**Request:**
```http
GET /api/session/state
```

**Response:**
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

**Fields:**
- `pedalboard_name` (string): Current pedalboard name or empty string
- `snapshot_name` (string): Current snapshot name or empty string
- `pedalboard_path` (string): Filesystem path to pedalboard bundle or empty string
- `pedalboard_size` (object): Canvas dimensions with `width` and `height` in pixels
- `hardware_profile` (array): Hardware actuator configurations for current device

**Used in:** `index.html` template

---

## 2. User Favorites Endpoint

### GET /api/user/favorites

**Purpose:** Get user's favorite plugins for index.html template

**Request:**
```http
GET /api/user/favorites
```

**Response:**
```json
{
  "favorites": [
    "http://calf.sourceforge.net/plugins/Reverb",
    "http://guitarix.sourceforge.net/plugins/gx_reverb",
    "urn:moddevices:GxSlowGear"
  ]
}
```

**Fields:**
- `favorites` (array): List of LV2 plugin URIs that the user has marked as favorites

**Used in:** `index.html` template for favorite plugins list

---

## 3. User Preferences Endpoint

### GET /api/user/preferences

**Purpose:** Get user preferences/settings for index.html template

**Request:**
```http
GET /api/user/preferences
```

**Response:**
```json
{
  "preferences": {
    "theme": "dark",
    "autoSave": true,
    "defaultGain": 0.8,
    "midiChannel": 1,
    "bufferSize": 256,
    "sampleRate": 48000
  }
}
```

**Fields:**
- `preferences` (object): Key-value pairs of user preferences and settings

**Used in:** `index.html` template for user configuration

---

## 4. Pedalboard Info Endpoint

### GET /api/pedalboard/info

**Purpose:** Get detailed pedalboard information for pedalboard.html template

**Request:**
```http
GET /api/pedalboard/info?bundlepath=/path/to/pedalboard.pedalboard
```

**Query Parameters:**
- `bundlepath` (string, required): URL-encoded path to the pedalboard bundle

**Response:**
```json
{
  "title": "My Awesome Pedalboard",
  "width": 1200,
  "height": 800,
  "connections": [
    {
      "source": "system:capture_1",
      "target": "effect_1:input"
    },
    {
      "source": "effect_1:output", 
      "target": "effect_2:input"
    }
  ],
  "plugins": [
    {
      "instance": "effect_1",
      "uri": "http://calf.sourceforge.net/plugins/Reverb",
      "x": 100,
      "y": 200,
      "parameters": {
        "gain": 0.5,
        "decay": 2.0
      }
    }
  ],
  "hardware": {
    "audio_ins": 2,
    "audio_outs": 2,
    "midi_ins": 1,
    "midi_outs": 1
  }
}
```

**Fields:**
- `title` (string): Pedalboard display name
- `width` (number): Canvas width in pixels
- `height` (number): Canvas height in pixels
- `connections` (array): Audio/MIDI connections between plugins and ports
- `plugins` (array): Plugin instances with positions and parameters
- `hardware` (object): Hardware I/O configuration

**Used in:** `pedalboard.html` template for viewing/editing specific pedalboards

---

## 5. Plugin GUIs Endpoint

### GET /api/plugins/guis

**Purpose:** Get all available plugin GUIs for allguis.html template

**Request:**
```http
GET /api/plugins/guis
```

**Response:**
```json
{
  "plugins": {
    "http://calf.sourceforge.net/plugins/Reverb": {
      "name": "Calf Reverb",
      "brand": "Calf",
      "category": ["Reverb"],
      "gui": {
        "resourcesDirectory": "/usr/lib/lv2/calf.lv2/",
        "iconTemplate": "reverb.html",
        "settingsTemplate": "reverb-settings.html", 
        "stylesheet": "reverb.css",
        "javascript": "reverb.js",
        "screenshot": "reverb.png",
        "thumbnail": "reverb-thumb.png"
      }
    }
  }
}
```

**Fields:**
- `plugins` (object): Map of plugin URIs to plugin GUI information
  - Each plugin contains:
    - `name` (string): Human-readable plugin name
    - `brand` (string): Plugin manufacturer/author
    - `category` (array): Plugin categories/tags
    - `gui` (object): GUI resource paths and templates

**Used in:** `allguis.html` template for displaying all plugin interfaces

---

## Implementation Notes

### Error Handling
All endpoints should return appropriate HTTP status codes:
- `200 OK`: Successful response with data
- `400 Bad Request`: Invalid parameters (e.g., missing bundlepath)
- `404 Not Found`: Resource doesn't exist (e.g., pedalboard not found)
- `500 Internal Server Error`: Server-side errors

### Timeout Considerations
The webserver calls these APIs with timeouts:
- Session state: 5 seconds
- User data (favorites/preferences): 5 seconds  
- Pedalboard info: 10 seconds
- Plugin GUIs: 10 seconds

### Fallback Behavior
If any API call fails, the webserver uses these defaults:

**Session State:**
```json
{
  "pedalboard_name": "",
  "snapshot_name": "",
  "pedalboard_path": "", 
  "pedalboard_size": {"width": 800, "height": 600},
  "hardware_profile": []
}
```

**User Data:**
```json
{
  "favorites": [],
  "preferences": {}
}
```

**Pedalboard Info:**
```json
{
  "title": "",
  "width": 0,
  "height": 0,
  "connections": [],
  "plugins": [],
  "hardware": {}
}
```

**Plugin GUIs:**
```json
{
  "plugins": {}
}
```

### Example Backend Implementation

```python
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()

@app.get("/api/session/state")
async def get_session_state():
    # Get from your session manager
    return {
        "pedalboard_name": current_session.pedalboard_name,
        "snapshot_name": current_session.snapshot_name,
        "pedalboard_path": current_session.pedalboard_path,
        "pedalboard_size": {"width": 800, "height": 600},
        "hardware_profile": get_hardware_actuators()
    }

@app.get("/api/user/favorites") 
async def get_user_favorites():
    # Get from user storage
    return {"favorites": user_service.get_favorites()}

@app.get("/api/user/preferences")
async def get_user_preferences():
    # Get from user storage  
    return {"preferences": user_service.get_preferences()}

@app.get("/api/pedalboard/info")
async def get_pedalboard_info(bundlepath: str = Query(...)):
    # Parse and load pedalboard
    pedalboard = pedalboard_service.load_pedalboard(bundlepath)
    if not pedalboard:
        raise HTTPException(404, "Pedalboard not found")
    return pedalboard.to_dict()

@app.get("/api/plugins/guis")
async def get_plugin_guis():
    # Get all available plugin GUIs
    return {"plugins": plugin_service.get_all_guis()}
```

This completes the API interface needed to fully decouple the template system from local dependencies!