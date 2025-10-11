# MOD UI – Frontend ↔ Backend API Reference

This document lists all HTTP and WebSocket APIs that are defined in the backend and actively used by the frontend (HTML/JS) in this repository. For each API, you get the endpoint, method, request shape, response shape, and where it’s used in the fr- **POST /effect/parameter/set/**
  - **Description:** Set plugin parameter value (legacy endp## Pedalboards

- **GET /pedalboard/list**
  - **Description:** Get list of all available pedalboards
  - **Response:** Array of pedalboard metadata; default pedalboard normalized with title "Default".
  - **Example Response:**
    ```json
    [
      {
        "title": "My Rock Setup",
        "bundlepath": "/home/user/pedalboards/my-rock-setup.pedalboard",
        "broken": false,
        "factory": false,
        "hasScreenshot": true
      },
      {
        "title": "Default",
        "bundlepath": "",
        "broken": false,
        "factory": true,
        "hasScreenshot": false
      }
    ]
    ```
  - **Data Source:** `mod/host.py get_pedalboard_list()` - scans `~/pedalboards/` directory for `.pedalboard` bundles
  - **Used in:** html/js/desktop.js (pedalboard list/indexer), html/js/banks.js (thumbnails).

- **POST /pedalboard/save**
  - **Description:** Save current pedalboard state to file
  - **Form fields:** title (string), asNew: 0/1
  - **Example Request:** `title=My Rock Setup&asNew=1`
  - **Response:** { ok: boolean, bundlepath: string|null, title: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "bundlepath": "/home/user/pedalboards/my-rock-setup.pedalboard", 
      "title": "My Rock Setup"
    }
    ```
  - **Data Source:** `mod/host.py save()` - serializes current plugin state, connections, and parameters
  - **Files Created:** `.pedalboard` bundle with `manifest.ttl`, `graph.ttl`, screenshot.png
  - **Used in:** html/js/desktop.js (saveCurrentPedalboard via saveBox).

- **GET /pedalboard/pack_bundle/?bundlepath=\<abs-path>**
  - **Description:** Download pedalboard as compressed bundle for sharing
  - **Example:** `/pedalboard/pack_bundle/?bundlepath=/home/user/pedalboards/setup.pedalboard`
  - **Response:** tar.gz (binary). If recording exists, includes audio. Used for sharing to cloud.
  - **Data Source:** Filesystem - compresses entire `.pedalboard` directory + optional recording into tar.gz
  - **Used in:** html/js/desktop.js (SimpleTransference to cloud).

- **POST /pedalboard/load_bundle/**
  - **Description:** Load a pedalboard from file path into current session
  - **Form fields:** bundlepath (abs path), isDefault (optional: '1' to mark default)
  - **Example Request:** `bundlepath=/home/user/pedalboards/setup.pedalboard&isDefault=0`
  - **Response:** { ok: boolean, name: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "name": "My Rock Setup"
    }
    ```
  - **Data Source:** `mod/host.py load()` - parses `.pedalboard` bundle TTL files and recreates plugin graph
  - **Side Effects:** Multiple websocket messages (`loading_start`, `add`, `connect`, `param_set`, `loading_end`)
  - **Used in:** html/js/desktop.js (loadPedalboard), also on reset to load default.:** JSON-encoded string containing "symbol/instance/portsymbol/value" (historic quirk).
  - **Example Request:** `"param_set/effect_123/gain/0.75"`
  - **Response:** Boolean; true indicates it was scheduled OK.
  - **Data Source:** `mod/host.py param_set()` - forwards to mod-host audio engine
  - **Side Effects:** Sends websocket `param_set` message to all clients
  - **Used in:** html/js/desktop.js (ParameterSet), also live param_set over WS.

- **GET /effect/preset/load/\<instance>?uri=\<preset-uri>**
  - **Description:** Load a preset for a plugin instance
  - **Example:** `/effect/preset/load/effect_123?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#preset1`
  - **Response:** Boolean or truthy on success.
  - **Data Source:** `mod/host.py preset_load()` - LV2 preset data from plugin bundle
  - **Side Effects:** Sends websocket `preset` and multiple `param_set` messages
  - **Used in:** html/js/desktop.js (pluginPresetLoad).

- **GET /effect/preset/save_new/\<instance>?name=\<name>**
  - **Description:** Create a new preset from current plugin state
  - **Example:** `/effect/preset/save_new/effect_123?name=My_Custom_Preset`
  - **Response:** Preset reference from backend helper; treat truthy as success.
  - **Data Source:** `mod/host.py preset_save_new()` - captures current parameter values to LV2 preset format
  - **File Created:** New `.ttl` preset file in user's LV2 directory
  - **Used in:** html/js/desktop.js (pluginPresetSaveNew).

- **GET /effect/preset/save_replace/\<instance>?uri=\<preset-uri>&bundle=\<bundlepath>&name=\<name>**
  - **Description:** Overwrite an existing preset with current plugin state
  - **Example:** `/effect/preset/save_replace/effect_123?uri=file:///home/user/.lv2/preset.lv2/preset1.ttl&bundle=/home/user/.lv2/preset.lv2&name=Updated_Preset`
  - **Response:** Truthy/opaque; treat truthy as success.
  - **Data Source:** `mod/host.py preset_save_replace()` - overwrites existing LV2 preset file
  - **File Modified:** Existing `.ttl` preset file updated with current parameter values
  - **Used in:** html/js/desktop.js (pluginPresetSaveReplace).

- **GET /effect/preset/delete/\<instance>?uri=\<preset-uri>&bundle=\<bundlepath>**
  - **Description:** Delete an existing user preset
  - **Example:** `/effect/preset/delete/effect_123?uri=file:///home/user/.lv2/preset.lv2/preset1.ttl&bundle=/home/user/.lv2/preset.lv2`
  - **Response:** Boolean.
  - **Data Source:** `mod/host.py preset_delete()` - removes LV2 preset file from filesystem
  - **File Deleted:** `.ttl` preset file removed from user's LV2 directory
  - **Used in:** html/js/desktop.js (pluginPresetDelete).- Base URL: all endpoints are relative to the device UI origin (e.g., http://device-host/).
- Content types: unless noted, JSON responses use application/json; uploads/downloads can be binary.
- Status handling: many endpoints return boolean true/false; some wrap in objects like { ok: true }.
- Files/locations below refer to this repo, for quick tracing.

## WebSocket API

### Connection
- **Endpoint:** `/websocket`
- **Description:** Primary WebSocket connection for real-time communication
- **Usage:** `html/js/host.js`, `html/js/desktop.js`

### Messages Received (Frontend to Backend)
- `data_ready <counter>` - Indicates frontend is ready to receive more events
  - **Example:** `data_ready 42`
  - **Source:** `html/js/host.js` - sent after processing websocket events
- `param_set <instance>/<symbol> <value>` - Set plugin parameter value
  - **Example:** `param_set effect_123/gain 0.75`
  - **Source:** `html/js/desktop.js` - when user moves a knob/slider
- `patch_get <instance> <uri>` - Get LV2 patch property
  - **Example:** `patch_get effect_123 http://example.org/patch#filename`
  - **Source:** Plugin GUI requesting patch data
- `patch_set <instance> <uri> <valuetype> <valuedata>` - Set LV2 patch property  
  - **Example:** `patch_set effect_123 http://example.org/patch#filename s /path/to/file.wav`
  - **Source:** Plugin GUI setting patch data
- `plugin_pos <instance> <x> <y>` - Set plugin position on canvas
  - **Example:** `plugin_pos effect_123 150 200`
  - **Source:** `html/js/desktop.js` - when dragging plugins on canvas
- `pedalboard_size <width> <height>` - Set pedalboard canvas size
  - **Example:** `pedalboard_size 1200 800`
  - **Source:** `html/js/desktop.js` - when resizing pedalboard view

### Messages Sent (Backend to Frontend)

#### System & Device Messages
- `stop` - Session has been stopped
  - **Example:** `stop`
  - **Source:** `mod/session.py:105` - when websocket connection ends
- `ping` - Response to ping request
  - **Example:** `ping`  
  - **Source:** `mod/session.py:226` - response to `/ping` HTTP endpoint
- `cc-device-updated` - Control Chain device has been updated
  - **Example:** `cc-device-updated`
  - **Source:** `mod/session.py:99` - when Control Chain hardware changes
- `bufsize <size>` - Audio buffer size changed
  - **Example:** `bufsize 256`
  - **Source:** `mod/host.py:548` - when JACK buffer size changes
- `stats <cpu_load> <xruns>` - System performance statistics (CPU load %, xrun count)
  - **Example:** `stats 23.5 0`
  - **Source:** `mod/host.py:4752` - periodic system monitoring
- `sys_stats <mem_load> <cpu_freq> <cpu_temp>` - Extended system stats (memory %, CPU frequency, temperature)
  - **Example:** `sys_stats 45.2 1800000 65000`
  - **Source:** `mod/host.py:4789` - from `/proc/meminfo`, `/proc/cpuinfo`, thermal sensors
- `truebypass <left> <right>` - True bypass state (0/1 for left/right channels)
  - **Example:** `truebypass 1 1`
  - **Source:** `mod/host.py:660` - when hardware bypass relays change state

#### Transport & Tempo
- `transport <rolling> <beats_per_bar> <bpm> <sync_mode>` - Transport state and timing info
  - **Example:** `transport 1 4.0 120.0 none`
  - **Source:** `mod/host.py:1830, 1893, 3658, 4555` - from JACK transport or internal tempo
  - `rolling`: 0/1 for stopped/playing
  - `sync_mode`: "none", "midi", "ableton_link", etc.

#### Hardware Ports
- `add_hw_port <port_path> <type> <is_output> <title> <index>` - Hardware port added
  - **Example:** `add_hw_port /graph/capture_1 audio 0 Capture_1 1`
  - **Source:** `mod/host.py:565, 579, 622, 2070, 2076` - from JACK port discovery
  - `type`: "audio", "midi", "cv"
  - `is_output`: 0 for input, 1 for output
- `remove_hw_port <port_path>` - Hardware port removed
  - **Example:** `remove_hw_port /graph/capture_1`
  - **Source:** `mod/host.py:650, 6837, 6848` - when JACK ports are removed

#### Plugin Management
- `add <instance> <uri> <x> <y> <bypassed> <version> <enabled>` - Plugin added to pedalboard
  - **Example:** `add effect_123 http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus 150.0 200.0 0 0 1`
  - **Source:** `mod/host.py:2591, 3863` - when plugins are instantiated via `/effect/add`
- `remove <instance>` - Plugin removed from pedalboard
  - **Example:** `remove effect_123`
  - **Source:** `mod/host.py:2696` - when plugin is removed via `/effect/remove`
- `remove :all` - All plugins removed
  - **Example:** `remove :all`
  - **Source:** `mod/host.py:2296` - when pedalboard is reset
- `preset <instance> <preset_uri>` - Plugin preset changed
  - **Example:** `preset effect_123 http://guitarix.sourceforge.net/plugins/gx_chorus#preset1`
  - **Source:** `mod/host.py:2868, 3173, 3877, 6247` - when preset is loaded
- `preset <instance> null` - Plugin preset cleared
  - **Example:** `preset effect_123 null`
  - **Source:** `mod/host.py:3011` - when preset is cleared
- `param_set <instance> <symbol> <value>` - Plugin parameter value changed
  - **Example:** `param_set effect_123 gain 0.75`
  - **Source:** `mod/host.py:1691, 1764, 1816` - from LV2 host parameter changes
- `output_set <instance> <symbol> <value>` - Plugin output port value changed
  - **Example:** `output_set effect_123 level_out 0.82`
  - **Source:** `mod/host.py:1710` - from LV2 host output port monitoring
- `patch_set <instance> <writable> <uri> <valuetype> <valuedata>` - LV2 patch property set
  - **Example:** `patch_set effect_123 1 http://example.org/patch#file s /path/file.wav`
  - **Source:** `mod/host.py:1733, 3226` - from LV2 patch protocol
- `plugin_pos <instance> <x> <y>` - Plugin position changed (broadcast to other clients)
  - **Example:** `plugin_pos effect_123 150 200`
  - **Source:** `mod/session.py` websocket handler - broadcast to other connected clients

#### Audio Connections
- `connect <port_from> <port_to>` - Audio/MIDI connection made
  - **Example:** `connect effect_123/audio_out_1 effect_456/audio_in_1`
  - **Source:** `mod/host.py:638, 3414, 3955` - when JACK connections are established
- `disconnect <port_from> <port_to>` - Audio/MIDI connection removed
  - **Example:** `disconnect effect_123/audio_out_1 effect_456/audio_in_1`
  - **Source:** `mod/host.py:2694, 3426, 6914` - when JACK connections are removed

#### MIDI & Control Chain
- `midi_map <instance> <symbol> <channel> <controller> <minimum> <maximum>` - MIDI mapping created
  - **Example:** `midi_map effect_123 gain 1 7 0.0 1.0`
  - **Source:** `mod/host.py:1761, mod/addressings.py:765` - when MIDI CC mapping is created
- `hw_map <instance> <symbol> <actuator_uri> <min> <max> <steps> <label> <value> <operational_mode> <page> <subpage> <coloured> <momentary> <group_id> <feedback_id>` - Hardware control mapping
  - **Example:** `hw_map effect_123 gain /hmi/knob1 0.0 1.0 33 Gain 0.5 = 0 0 1 0 1 0 0`
  - **Source:** `mod/addressings.py:718, 738, 757` - when Control Chain hardware mapping is created
- `cv_map <instance> <symbol> <source> <minimum> <maximum> <operational_mode> <label> <feedback>` - CV mapping created
  - **Example:** `cv_map effect_123 gain /cv/input1 0.0 5.0 = CV_Input 0`
  - **Source:** `mod/addressings.py:780` - when CV addressing is created
- `hw_add <device_uri> <label> <labelsuffix> <version>` - Hardware device added
  - **Example:** `hw_add /hmi/footswitch1 Footswitch _1 1`
  - **Source:** `mod/host.py:933` - when Control Chain device is detected
- `hw_rem <device_uri> <label> <version>` - Hardware device removed  
  - **Example:** `hw_rem /hmi/footswitch1 Footswitch 1`
  - **Source:** `mod/host.py:939` - when Control Chain device is disconnected
- `hw_con <label> <version>` - Hardware device connected
  - **Example:** `hw_con Footswitch 1`
  - **Source:** `mod/host.py:942` - Control Chain device connection event
- `hw_dis <label> <version>` - Hardware device disconnected
  - **Example:** `hw_dis Footswitch 1`
  - **Source:** `mod/host.py:945` - Control Chain device disconnection event
- `act_add <base64_encoded_actuator_metadata>` - Hardware actuator added
  - **Example:** `act_add eyJ1cmkiOiIvaG1pL2Zvb3RzdzEiLCJuYW1lIjoiRm9vdHN3aXRjaCAxIn0=`
  - **Source:** `mod/host.py:948` - base64 encoded JSON metadata for new actuator from Control Chain
- `act_del <actuator_uri>` - Hardware actuator removed
  - **Example:** `act_del /hmi/footsw1`
  - **Source:** `mod/host.py:961` - when Control Chain actuator is removed
- `add_cv_port <actuator_uri> <name> <operational_mode>` - CV port added
  - **Example:** `add_cv_port /cv/input1 CV_Input =`
  - **Source:** `mod/addressings.py:682` - when CV input port becomes available

#### Pedalboard Loading
- `loading_start <is_default> <is_modified>` - Pedalboard loading started
  - **Example:** `loading_start 0 1`
  - **Source:** `mod/host.py:3490` - when pedalboard loading begins
- `loading_end <snapshot_id>` - Pedalboard loading finished
  - **Example:** `loading_end 0`
  - **Source:** `mod/host.py:3683, 2240` - when pedalboard loading completes
- `size <width> <height>` - Pedalboard canvas size set
  - **Example:** `size 1200 800`
  - **Source:** `mod/host.py:3491, 2029` - pedalboard canvas dimensions

#### Snapshots
- `pedal_snapshot <index> <name>` - Snapshot created/updated
  - **Example:** `pedal_snapshot 1 My_Snapshot`
  - **Source:** `mod/host.py:3253` - when snapshot is saved or loaded

#### Data Flow
- `data_ready <counter>` - Backend ready to send more data (response to frontend data_ready)
  - **Example:** `data_ready 42`
  - **Source:** `mod/host.py:1628` - flow control for websocket message queuing

#### Plugin Scanning
- `rescan <base64_encoded_plugin_data>` - Plugin rescan results (base64 encoded JSON)
  - **Example:** `rescan eyJwbHVnaW5zIjpbeyJ1cmkiOiJodHRwOi8vZ3VpdGFyaXguc291cmNlZm9yZ2UubmV0L3BsdWdpbnMvZ3hfY2hvcnVzI19jaG9ydXMiLCJuYW1lIjoiR3hDaG9ydXMifV19`
  - **Source:** `mod/webserver.py:787, 821, 1171` - when plugin database is rescanned

#### Logging
- `log <message>` - Log message from audio engine
  - **Example:** `log [mod-host] Plugin loaded: http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Source:** `mod/host.py:1855` - debug/info messages from mod-host audio engine

## Effects (Plugins)

- **GET /effect/list**
  - **Description:** Get list of all available plugins
  - **Response:** Array of plugin summaries (from get_all_plugins()).
  - **Example Response:**
    ```json
    [
      {
        "uri": "http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus",
        "name": "GxChorus", 
        "category": ["Modulator"],
        "version": "0.01",
        "microVersion": 0,
        "minorVersion": 1,
        "release": 0,
        "builder": "Guitarix team"
      }
    ]
    ```
  - **Data Source:** `mod/host.py` - LV2 plugin scanning using lilv library from system LV2 directories
  - **Used in:** html/js/effects.js (search/list), html/js/desktop.js (cloudPluginListFunction), html/js/cloudplugin.js.

- **POST /effect/bulk/**
  - **Description:** Get detailed info for multiple plugins at once
  - **Request:** JSON array of plugin URIs.
  - **Example Request:**
    ```json
    [
      "http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus",
      "http://calf.sourceforge.net/plugins/Reverb"
    ]
    ```
  - **Response:** Object mapping uri -> full plugin info (from get_plugin_info()).
  - **Example Response:**
    ```json
    {
      "http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus": {
        "uri": "http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus",
        "name": "GxChorus",
        "ports": {
          "control": [...],
          "audio": {...},
          "midi": {...}
        },
        "presets": [...]
      }
    }
    ```
  - **Data Source:** `mod/host.py get_plugin_info()` - detailed LV2 plugin introspection using lilv
  - **Used in:** html/js/desktop.js (getPluginsData, installMissingPlugins).

- **GET /effect/get?uri=\<uri>&version=\<v>&plugin_version=\<v>**
  - **Description:** Get detailed information about a specific plugin
  - **Query:** uri (required). Additional params are ignored server-side but passed by frontend.
  - **Example:** `/effect/get?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** Full plugin info (from get_plugin_info()).
  - **Example Response:** Same detailed structure as in bulk/ endpoint above
  - **Data Source:** `mod/host.py get_plugin_info()` - cached LV2 plugin data using lilv
  - **Used in:** html/js/effects.js, html/js/pedalboard.js, html/js/host.js, html/js/cloudplugin.js.

- **GET /effect/get_non_cached?uri=\<uri>**
  - **Description:** Get plugin info bypassing cache (forces fresh scan)
  - **Example:** `/effect/get_non_cached?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** Full plugin info without using cache.
  - **Data Source:** `mod/host.py get_plugin_info()` - fresh LV2 plugin scan, bypasses internal cache
  - **Used in:** html/js/modgui.js.

- **GET /effect/add/\<instance>?uri=\<uri>&x=\<float>&y=\<float>**
  - **Description:** Add a plugin to the current pedalboard
  - **Example:** `/effect/add/effect_123?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus&x=150.5&y=200.0`
  - **Response:** Full plugin info of the added effect on success; false on failure.
  - **Data Source:** `mod/host.py add_plugin()` - LV2 plugin instantiation via mod-host
  - **Side Effects:** Sends websocket `add` message to all clients
  - **Used in:** html/js/desktop.js (pluginLoad callback in pedalboard).

- **GET /effect/remove/\<instance>**
  - **Description:** Remove a plugin from the current pedalboard
  - **Example:** `/effect/remove/effect_123`
  - **Response:** Boolean.
  - **Data Source:** `mod/host.py remove_plugin()` - removes plugin instance from mod-host
  - **Side Effects:** Sends websocket `remove` message to all clients
  - **Used in:** html/js/desktop.js.

- **GET /effect/connect/\<fromPort>,\<toPort>**
  - **Description:** Create an audio/MIDI connection between two ports
  - **Example:** `/effect/connect/effect_123/audio_out_1,effect_456/audio_in_1`
  - **Response:** Boolean.
  - **Data Source:** `mod/host.py connect()` - creates JACK connection via mod-host
  - **Side Effects:** Sends websocket `connect` message to all clients
  - **Used in:** html/js/desktop.js (portConnect), html/js/pedalboard.js.

- **GET /effect/disconnect/\<fromPort>,\<toPort>**
  - **Description:** Remove an audio/MIDI connection between two ports
  - **Example:** `/effect/disconnect/effect_123/audio_out_1,effect_456/audio_in_1`
  - **Response:** Boolean.
  - **Data Source:** `mod/host.py disconnect()` - removes JACK connection via mod-host
  - **Side Effects:** Sends websocket `disconnect` message to all clients
  - **Used in:** html/js/desktop.js (portDisconnect).

- **POST /effect/parameter/address/\<instanceAndSymbol>**
  - **Description:** Map a plugin parameter to a hardware control or MIDI CC
  - **Example URL:** `/effect/parameter/address/effect_123/gain`
  - **Request:** JSON object with addressing parameters:
    - Required: uri, label, minimum, maximum, value
    - Optional: steps (default 33), tempo (bool), dividers, page (int), subpage (int), coloured, momentary, operationalMode
  - **Example Request:**
    ```json
    {
      "uri": "/hmi/knob1",
      "label": "Gain",
      "minimum": 0.0,
      "maximum": 1.0, 
      "value": 0.5,
      "steps": 33
    }
    ```
  - **Response:** Boolean (true on success).
  - **Data Source:** `mod/host.py address()` - creates mapping in addressings system and Control Chain/MIDI
  - **Side Effects:** Sends websocket `hw_map` or `midi_map` message to all clients
  - **Used in:** html/js/desktop.js (hardwareManager.address, unaddressPort), html/js/transport.js.

- POST /effect/parameter/set/
  - Request: JSON-encoded string containing "symbol/instance/portsymbol/value" (historic quirk).
  - Response: Boolean; true indicates it was scheduled OK.
  - Used in: html/js/desktop.js (ParameterSet), also live param_set over WS.

- GET /effect/preset/load/<instance>?uri=<preset-uri>
  - Response: Boolean or truthy on success.
  - Used in: html/js/desktop.js (pluginPresetLoad).

- GET /effect/preset/save_new/<instance>?name=<name>
  - Response: Preset reference from backend helper; treat truthy as success.
  - Used in: html/js/desktop.js (pluginPresetSaveNew).

- GET /effect/preset/save_replace/<instance>?uri=<preset-uri>&bundle=<bundlepath>&name=<name>
  - Response: Truthy/opaque; treat truthy as success.
  - Used in: html/js/desktop.js (pluginPresetSaveReplace).

- GET /effect/preset/delete/<instance>?uri=<preset-uri>&bundle=<bundlepath>
  - Response: Boolean.
  - Used in: html/js/desktop.js (pluginPresetDelete).

- **GET /effect/image/(screenshot|thumbnail).png?uri=\<uri>&v=\<ver>**
  - **Description:** Get plugin GUI screenshot or thumbnail image
  - **Example:** `/effect/image/screenshot.png?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus&v=1`
  - **Response:** Image (PNG). Falls back to defaults if missing.
  - **Data Source:** Plugin LV2 bundle `modgui/` directory or generated screenshots
  - **Fallback:** Default MOD plugin images if plugin-specific images not found
  - **Used in:** html/js/effects.js, html/js/cloudplugin.js (thumbnail/screenshot displays).

- **GET /effect/file/(iconTemplate|settingsTemplate|stylesheet|javascript)**
  - **Description:** Get plugin GUI template files and resources
  - **Query:** uri=<plugin-uri>
  - **Example:** `/effect/file/iconTemplate?uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** Text content (text/plain; charset=UTF-8). For custom .wasm: application/wasm
  - **Data Source:** Plugin LV2 bundle `modgui/` directory files (template.html, style.css, etc.)
  - **File Types:** 
    - iconTemplate: `template.html` - HTML GUI template
    - settingsTemplate: `settings.html` - Settings dialog template  
    - stylesheet: `stylesheet.css` - CSS styles
    - javascript: `script.js` - JavaScript behavior
  - **Used in:** html/js/modgui.js (loads GUI templates, CSS, JS, documentation file via documentation).

- **GET /effect/file/custom?filename=\<relative>&uri=\<plugin-uri>**
  - **Description:** Get custom plugin GUI assets (images, WASM, etc.)
  - **Example:** `/effect/file/custom?filename=knob.png&uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** File content; type inferred (wasm handled specially).
  - **Data Source:** Plugin LV2 bundle `modgui/` directory, arbitrary files referenced by GUI templates
  - **MIME Types:** Inferred from file extension, special handling for .wasm files
  - **Used in:** html/js/modgui.js (custom GUI assets).

## Pedalboards

- GET /pedalboard/list
  - Response: Array of pedalboard metadata; default pedalboard normalized with title “Default”.
  - Used in: html/js/desktop.js (pedalboard list/indexer), html/js/banks.js (thumbnails).

- POST /pedalboard/save
  - Form fields: title (string), asNew: 0/1
  - Response: { ok: boolean, bundlepath: string|null, title: string }
  - Used in: html/js/desktop.js (saveCurrentPedalboard via saveBox).

- GET /pedalboard/pack_bundle/?bundlepath=<abs-path>
  - Response: tar.gz (binary). If recording exists, includes audio. Used for sharing to cloud.
  - Used in: html/js/desktop.js (SimpleTransference to cloud).

- POST /pedalboard/load_bundle/
  - Form fields: bundlepath (abs path), isDefault (optional: '1' to mark default)
  - Response: { ok: boolean, name: string }
  - Used in: html/js/desktop.js (loadPedalboard), also on reset to load default.

- **POST /pedalboard/load_web/**
  - **Description:** Upload and load a pedalboard bundle from file upload
  - **Body:** uploaded tar.gz (multipart/binary)
  - **Example:** Binary tar.gz file containing `.pedalboard` directory structure
  - **Response:** { ok: true } on success
  - **Data Source:** Uploaded file extracted to temporary location, then loaded via `mod/host.py load()`
  - **File Operations:** Extracts tar.gz, validates `.pedalboard` structure, moves to user's pedalboards directory
  - **Side Effects:** Same websocket messages as load_bundle/
  - **Used in:** html/js/desktop.js (loadRemotePedalboard via SimpleTransference).

- **GET /pedalboard/factorycopy/?bundlepath=\<abs-path>&title=\<string>**
  - **Description:** Create a user copy of a factory/read-only pedalboard
  - **Example:** `/pedalboard/factorycopy/?bundlepath=/usr/share/pedalboards/factory.pedalboard&title=My Copy`
  - **Response:** Full pedalboard info for the new copy (with bundlepath/title adjusted).
  - **Example Response:**
    ```json
    {
      "ok": true,
      "bundlepath": "/home/user/pedalboards/my-copy.pedalboard",
      "title": "My Copy",
      "plugins": [...],
      "connections": [...]
    }
    ```
  - **Data Source:** `mod/host.py factorycopy()` - copies factory pedalboard to user's directory
  - **File Operations:** Recursive copy from factory location to `~/pedalboards/` with new name
  - **Used in:** html/js/desktop.js (BankBox copyFactoryPedalboard).

- **GET /pedalboard/info/?bundlepath=\<abs-path>**
  - **Description:** Get detailed pedalboard information without loading it
  - **Example:** `/pedalboard/info/?bundlepath=/home/user/pedalboards/setup.pedalboard`
  - **Response:** Full pedalboard info (plugins, connections, etc.).
  - **Example Response:**
    ```json
    {
      "title": "My Rock Setup",
      "plugins": [
        {
          "instance": "effect_123",
          "uri": "http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus",
          "x": 150, "y": 200,
          "ports": {...}
        }
      ],
      "connections": [
        ["effect_123/audio_out_1", "effect_456/audio_in_1"]
      ]
    }
    ```
  - **Data Source:** `mod/host.py get_pedalboard_info()` - parses `.pedalboard` TTL files without loading
  - **Used in:** html/js/desktop.js (loading broken factory PBs).

- **GET /pedalboard/remove/?bundlepath=\<abs-path>**
  - **Description:** Delete a pedalboard from the filesystem
  - **Example:** `/pedalboard/remove/?bundlepath=/home/user/pedalboards/old-setup.pedalboard`
  - **Response:** Boolean.
  - **Data Source:** `mod/host.py remove_pedalboard()` - removes entire `.pedalboard` directory
  - **File Operations:** Recursive deletion of pedalboard bundle directory
  - **Used in:** html/js/desktop.js (remove pedalboard).

- **GET /pedalboard/image/(screenshot|thumbnail).png?bundlepath=\<abs-path>&tstamp=\<num>&v=\<ver>**
  - **Description:** Get pedalboard screenshot or thumbnail image
  - **Example:** `/pedalboard/image/screenshot.png?bundlepath=/home/user/pedalboards/setup.pedalboard&tstamp=1633024800&v=1`
  - **Response:** Image (PNG).
  - **Data Source:** `screenshot.png` or `thumbnail.png` file within `.pedalboard` bundle
  - **Cache Control:** tstamp and v parameters used for browser cache busting
  - **Fallback:** Default blank pedalboard image if screenshot not available
  - **Used in:** html/js/banks.js (thumbnail display).

- **GET /pedalboard/image/generate?bundlepath=\<abs-path>**
  - **Description:** Trigger asynchronous generation of pedalboard screenshot
  - **Example:** `/pedalboard/image/generate?bundlepath=/home/user/pedalboards/setup.pedalboard`
  - **Response:** { ok: boolean, ctime: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "ctime": "1633024800.123"
    }
    ```
  - **Data Source:** `mod/screenshot.py` - renders current pedalboard canvas to PNG file
  - **File Created:** `screenshot.png` within the `.pedalboard` bundle directory
  - **Async Process:** Screenshot generation runs in background, doesn't block request
  - **Used in:** html/js/desktop.js (waitForScreenshot generate step).

- **GET /pedalboard/image/wait?bundlepath=\<abs-path>**
  - **Description:** Wait for screenshot generation to complete
  - **Example:** `/pedalboard/image/wait?bundlepath=/home/user/pedalboards/setup.pedalboard`
  - **Response:** { ok: boolean, ctime: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "ctime": "1633024800.456"
    }
    ```
  - **Data Source:** Monitors screenshot file creation timestamp and generation process status
  - **Behavior:** Blocks until screenshot generation completes or times out
  - **Used in:** html/js/desktop.js (waitForScreenshot wait step).

- GET /pedalboard/image/check?bundlepath=<abs-path>&v=<ver>
  - Response: { status: 0|1|other, ctime: string }
  - Used in: html/js/common.js wait_for_pedalboard_screenshot.

- POST /pedalboard/cv_addressing_plugin_port/add
  - Form fields: uri (string), name (string)
  - Response: { ok: true, operational_mode: string|number }
  - Used in: html/js/desktop.js (addCVAddressingPluginPort).

- POST /pedalboard/cv_addressing_plugin_port/remove
  - Form fields: uri (string)
  - Response: Boolean (or backend-structured JSON)
  - Used in: html/js/desktop.js (removeCVAddressingPluginPort).

- POST /pedalboard/transport/set_sync_mode/<mode>
  - Path param mode: /none | /midi_clock_slave | /link
  - Response: Boolean
  - Used in: html/js/desktop.js (transportControls.setSyncMode).

## Snapshots (Pedalboard Presets)

- **POST /snapshot/save**
  - **Description:** Save current plugin parameter states as a snapshot
  - **Response:** Boolean
  - **Data Source:** `mod/host.py snapshot_save()` - captures current parameter values for all plugins
  - **Storage:** Saved within current pedalboard's `.pedalboard` bundle as TTL data
  - **Side Effects:** Sends websocket `pedal_snapshot` message with snapshot index and name
  - **Used in:** html/js/desktop.js (snapshotSaveButton).

- **GET /snapshot/saveas?title=\<string>**
  - **Description:** Save current state as a new named snapshot
  - **Example:** `/snapshot/saveas?title=My Custom Tone`
  - **Response:** { ok: boolean, id: number, title: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "id": 3,
      "title": "My Custom Tone"
    }
    ```
  - **Data Source:** `mod/host.py snapshot_saveas()` - creates new snapshot with incremented ID
  - **Storage:** Adds new snapshot data to pedalboard's TTL files
  - **Used in:** html/js/desktop.js (snapshotSaveAsButton flow).

- **GET /snapshot/rename?id=\<number>&title=\<string>**
  - **Description:** Change the name of an existing snapshot
  - **Example:** `/snapshot/rename?id=3&title=Updated Tone`
  - **Response:** { ok: boolean, title: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "title": "Updated Tone"
    }
    ```
  - **Data Source:** `mod/host.py snapshot_rename()` - updates snapshot metadata in pedalboard
  - **Storage:** Modifies existing snapshot TTL data
  - **Used in:** html/js/snapshot.js (pedalPresetRenamed).

- **GET /snapshot/remove?id=\<number>**
  - **Description:** Delete a snapshot
  - **Example:** `/snapshot/remove?id=3`
  - **Response:** Boolean
  - **Data Source:** `mod/host.py snapshot_remove()` - removes snapshot from pedalboard data
  - **Storage:** Deletes snapshot TTL data from pedalboard bundle
  - **Used in:** html/js/snapshot.js.

- **GET /snapshot/list**
  - **Description:** Get all snapshots for current pedalboard
  - **Response:** Object mapping snapshot index -> name
  - **Example Response:**
    ```json
    {
      "0": "Default",
      "1": "Clean Tone",
      "2": "Distorted",
      "3": "My Custom Tone"
    }
    ```
  - **Data Source:** `mod/host.py snapshot_list()` - reads snapshot data from current pedalboard
  - **Used in:** html/js/snapshot.js (populate preset list).

- **GET /snapshot/name?id=\<number>**
  - **Description:** Get the name of a specific snapshot
  - **Example:** `/snapshot/name?id=2`
  - **Response:** { ok: boolean, name: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "name": "Distorted"
    }
    ```
  - **Data Source:** `mod/host.py snapshot_name()` - looks up snapshot name by ID
  - **Used in:** html/js/host.js (display current snapshot name).

- **GET /snapshot/load?id=\<number>**
  - **Description:** Load a snapshot, restoring all parameter values
  - **Example:** `/snapshot/load?id=2`
  - **Response:** Boolean
  - **Data Source:** `mod/host.py snapshot_load()` - retrieves saved parameter values and applies them
  - **Side Effects:** Multiple websocket `param_set` messages sent to all clients as parameters change
  - **Audio Engine:** Parameter changes sent to mod-host to update actual plugin values
  - **Used in:** html/js/snapshot.js (load on select).

## Banks

- **GET /banks**
  - **Description:** Get organized collections of pedalboards grouped into banks
  - **Response:** Array of banks with pedalboards (each pedalboard contains full info object).
  - **Example Response:**
    ```json
    [
      {
        "title": "Rock",
        "pedalboards": [
          {
            "title": "Heavy Distortion",
            "bundlepath": "/home/user/pedalboards/heavy.pedalboard",
            "broken": false,
            "hasScreenshot": true
          },
          {
            "title": "Clean Rock",
            "bundlepath": "/home/user/pedalboards/clean.pedalboard", 
            "broken": false,
            "hasScreenshot": true
          }
        ]
      },
      {
        "title": "Jazz",
        "pedalboards": [...]
      }
    ]
    ```
  - **Data Source:** `mod/host.py get_banks()` - reads bank configuration and associated pedalboards
  - **Storage:** Bank organization stored in user preferences or separate bank configuration file
  - **Used in:** html/js/desktop.js (BankBox load), html/js/banks.js (UI).

- **POST /banks/save**
  - **Description:** Save bank organization and pedalboard groupings
  - **Request:** JSON array/object with banks structure.
  - **Example Request:**
    ```json
    [
      {
        "title": "Rock",
        "pedalboards": [
          "/home/user/pedalboards/heavy.pedalboard",
          "/home/user/pedalboards/clean.pedalboard"
        ]
      },
      {
        "title": "Jazz", 
        "pedalboards": [
          "/home/user/pedalboards/smooth.pedalboard"
        ]
      }
    ]
    ```
  - **Response:** Boolean
  - **Data Source:** `mod/host.py save_banks()` - persists bank organization to configuration file
  - **Storage:** Writes bank structure to user preferences or dedicated bank config file
  - **Used in:** html/js/desktop.js (BankBox save).

## Favorites

- **POST /favorites/add**
  - **Description:** Add a plugin to user's favorites list
  - **Form fields:** uri (string)
  - **Example Request:** `uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** Boolean
  - **Data Source:** `mod/host.py favorites_add()` - adds plugin URI to user's favorites list
  - **Storage:** Saved in user preferences file (`~/.config/mod-ui/preferences.json`)
  - **Used in:** html/js/effects.js (mark as favorite).

- **POST /favorites/remove**
  - **Description:** Remove a plugin from user's favorites list
  - **Form fields:** uri (string)
  - **Example Request:** `uri=http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus`
  - **Response:** Boolean
  - **Data Source:** `mod/host.py favorites_remove()` - removes plugin URI from user's favorites list
  - **Storage:** Updated in user preferences file
  - **Used in:** html/js/effects.js (unfavorite).

## Recording and Sharing

- **GET /recording/start**
  - **Description:** Start recording audio from the current pedalboard
  - **Response:** Boolean
  - **Data Source:** `mod/session.py web_recording_start()` - initializes audio recording via recorder module
  - **Audio Source:** Records processed audio output from JACK, after all plugin processing
  - **File Storage:** Temporary audio file created in system temp directory
  - **Used in:** html/js/desktop.js (share flow, via ajaxFactory helpers).

- **GET /recording/stop**
  - **Description:** Stop audio recording and finalize the file
  - **Response:** Boolean
  - **Data Source:** `mod/session.py web_recording_stop()` - stops recording and closes audio file
  - **File Operations:** Finalizes temporary audio file for download/playback
  - **Used in:** html/js/desktop.js (share flow, via ajaxFactory helpers).

- **GET /recording/play/start**
  - **Description:** Start playback of the recorded audio
  - **Response:** Boolean
  - **Data Source:** `mod/session.py web_playing_start()` - begins playback through JACK audio system
  - **Audio Behavior:** Temporarily mutes live audio and plays back recorded file
  - **Used in:** html/js/desktop.js (share preview/playback flow).

- **GET /recording/play/wait**
  - **Description:** Wait for audio playback to complete
  - **Response:** Boolean; wait blocks until playback ends and returns true.
  - **Behavior:** Synchronous endpoint that blocks until playback finishes
  - **Used in:** html/js/desktop.js (share preview/playback flow).

- **GET /recording/play/stop**
  - **Description:** Stop audio playback immediately
  - **Response:** Boolean
  - **Data Source:** `mod/session.py web_playing_stop()` - stops playback and restores live audio
  - **Audio Behavior:** Unmutes live audio processing
  - **Used in:** html/js/desktop.js (share preview/playback flow).

- **GET /recording/download**
  - **Description:** Download the recorded audio file
  - **Response:** { ok: boolean, audio: base64-encoded audio or "" }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."
    }
    ```
  - **Data Source:** `mod/session.py web_recording_download()` - reads recorded audio file and base64 encodes it
  - **Format:** WAV audio file encoded as base64 string for web transfer
  - **Used in:** html/js/desktop.js (share recording download).

- **GET /recording/reset**
  - **Description:** Clear/delete the current recording
  - **Response:** Boolean
  - **Data Source:** `mod/session.py web_recording_delete()` - removes temporary recording file
  - **File Operations:** Deletes temporary audio file from filesystem
  - **Used in:** html/js/desktop.js (share flow reset).

- **GET /save_user_id/**
  - **Description:** Store user identity information for sharing features
  - **Form fields:** name, email
  - **Example Request:** `name=John Doe&email=john@example.com`
  - **Response:** Boolean
  - **Data Source:** User preferences system - saves identity info for pedalboard sharing
  - **Storage:** Saved in user preferences file for future sharing operations
  - **Used in:** html/js/desktop.js (share flow, store user identity).

## Device/Network/Performance Controls

- **GET /ping**
  - **Description:** Check HMI (Hardware Machine Interface) connection status and latency
  - **Response:** { ihm_online: boolean, ihm_time: number(ms) }
  - **Example Response:**
    ```json
    {
      "ihm_online": true,
      "ihm_time": 23.5
    }
    ```
  - **Data Source:** `mod/session.py web_ping()` - tests HMI serial communication and measures response time
  - **Hardware Test:** Sends ping command to MOD hardware and measures round-trip time
  - **Side Effects:** Sends websocket `ping` message to all clients
  - **Used in:** html/js/networkstatus.js.

- **GET /reset**
  - **Description:** Reset current session to empty pedalboard state
  - **Response:** Boolean
  - **Data Source:** `mod/session.py reset()` - clears all plugins, connections, and resets to default state
  - **Side Effects:** Multiple websocket messages (`stop`, `remove :all`, `loading_start`, `loading_end`)
  - **Hardware:** Updates HMI display to show empty pedalboard
  - **Used in:** html/js/desktop.js (pedalboard reset action).

- **GET /truebypass/(Left|Right)/(true|false)**
  - **Description:** Control hardware true bypass relays for direct audio routing
  - **Example:** `/truebypass/Left/true`, `/truebypass/Right/false`
  - **Response:** Boolean
  - **Data Source:** `mod/host.py set_truebypass()` - controls physical bypass relays in MOD hardware
  - **Hardware Effect:** Physically routes input directly to output, bypassing all digital processing
  - **Side Effects:** Sends websocket `truebypass` message with current bypass state
  - **Used in:** html/js/desktop.js (bypass buttons).

- **POST /set_buffersize/(128|256)**
  - **Description:** Change JACK audio buffer size for latency vs. stability tradeoff
  - **Example:** `/set_buffersize/128`, `/set_buffersize/256`
  - **Response:** { ok: boolean, size: number }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "size": 128
    }
    ```
  - **Data Source:** `mod/host.py set_buffer_size()` - reconfigures JACK audio system buffer size
  - **Audio Impact:** Lower values = lower latency but higher CPU usage and potential dropouts
  - **Side Effects:** Sends websocket `bufsize` message with new buffer size
  - **Used in:** html/js/desktop.js (buffer size toggle).

- **POST /reset_xruns/**
  - **Description:** Reset JACK audio dropout (xrun) counter to zero
  - **Response:** Boolean
  - **Data Source:** `mod/host.py reset_xruns()` - clears JACK xrun statistics
  - **Audio Context:** XRuns are audio dropouts caused by buffer underruns/overruns
  - **Monitoring:** Allows user to reset counter after fixing audio configuration issues
  - **Used in:** html/js/desktop.js (reset XRuns).

- **POST /switch_cpu_freq/**
  - **Description:** Toggle CPU frequency scaling between performance and powersave modes
  - **Response:** Boolean
  - **Data Source:** `mod/host.py switch_cpu_freq()` - changes system CPU governor via sysfs
  - **System Impact:** Performance mode = higher CPU frequency but more power consumption
  - **File Operations:** Writes to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
  - **Used in:** html/js/desktop.js (CPU stats button toggles freq).

- **POST /config/set**
  - **Description:** Save user interface configuration settings
  - **Form fields:** key, value
  - **Example Request:** `key=canvas_zoom&value=1.2`
  - **Response:** Boolean
  - **Data Source:** `mod/session.py` user preferences system - saves UI settings and preferences
  - **Storage:** Written to user preferences file (`~/.config/mod-ui/preferences.json`)
  - **Settings Types:** Canvas zoom, theme preferences, UI layout options, etc.
  - **Used in:** html/js/desktop.js (saveConfigValue for UI settings/preferences).

## MIDI Devices (JACK)

- **GET /jack/get_midi_devices**
  - **Description:** Get list of available MIDI devices and current configuration
  - **Response:** { devsInUse, devList, names, midiAggregatedMode }
  - **Example Response:**
    ```json
    {
      "devsInUse": ["hw:1,0,0"],
      "devList": ["hw:1,0,0", "hw:2,0,0"],
      "names": {
        "hw:1,0,0": "USB MIDI Device",
        "hw:2,0,0": "Built-in MIDI"
      },
      "midiAggregatedMode": true
    }
    ```
  - **Data Source:** `mod/host.py get_midi_ports()` - scans JACK MIDI system for available devices
  - **Hardware Detection:** Queries JACK for connected MIDI interfaces and their capabilities
  - **Used in:** html/js/mididevices.js (render device list).

- **POST /jack/set_midi_devices**
  - **Description:** Configure which MIDI devices are active and their routing mode
  - **Request:** JSON { devs: [...], midiAggregatedMode: bool, midiLoopback: bool }
  - **Example Request:**
    ```json
    {
      "devs": ["hw:1,0,0", "hw:2,0,0"],
      "midiAggregatedMode": true,
      "midiLoopback": false
    }
    ```
  - **Response:** Boolean
  - **Data Source:** `mod/host.py set_midi_devices()` - configures JACK MIDI routing and creates/removes ports
  - **JACK Operations:** Creates MIDI merger/broadcaster ports, connects/disconnects MIDI devices
  - **Side Effects:** Websocket messages for `add_hw_port`/`remove_hw_port` as MIDI ports change
  - **Used in:** html/js/mididevices.js (apply settings).

## File System Listing (User Files)

- **GET /files/list?types=\<comma-separated>**
  - **Description:** List user files of specific types for plugin file selectors
  - **Query Parameters:** types values: audioloop, audiorecording, audiosample, audiotrack, cabsim, h2drumkit, ir, midiclip, midisong, sf2, sfz, aidadspmodel, nammodel
  - **Example:** `/files/list?types=audiosample,ir,sf2`
  - **Response:** { ok: true, files: [ { fullname, basename, filetype } ] }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "files": [
        {
          "fullname": "/home/user/audio/guitar_sample.wav",
          "basename": "guitar_sample.wav", 
          "filetype": "audiosample"
        },
        {
          "fullname": "/home/user/impulses/hall_reverb.wav",
          "basename": "hall_reverb.wav",
          "filetype": "ir"
        }
      ]
    }
    ```
  - **Data Source:** Filesystem scan of user directories (`~/audio/`, `~/impulses/`, etc.) filtered by file extensions
  - **File Types:** Audio samples, impulse responses, SoundFont files, hydrogen drumkits, AIDA-X models, etc.
  - **Used in:** html/js/modgui.js (file selectors inside plugin UIs).

## Authentication with MOD Cloud

- **POST /auth/nonce**
  - **Description:** Handle authentication nonce from MOD Cloud service
  - **Request:** JSON forwarded from cloud /devices/nonce: { nonce, ... }
  - **Example Request:**
    ```json
    {
      "nonce": "abc123xyz789",
      "device_id": "mod-device-001"
    }
    ```
  - **Response:** { message: string } or {} if unsupported token module.
  - **Data Source:** MOD Cloud authentication service - validates device identity
  - **Crypto Operations:** Processes cryptographic nonce for secure device registration
  - **Used in:** html/js/desktop.js (authenticateDevice flow).

- **POST /auth/token**
  - **Description:** Store authentication token from MOD Cloud for API access
  - **Request:** JSON payload received from cloud /devices/tokens (encrypted/encoded string).
  - **Example Request:**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires": 1640995200
    }
    ```
  - **Response:** { access_token: string }
  - **Example Response:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
  - **Data Source:** MOD Cloud token service - provides JWT tokens for API authentication
  - **Storage:** Token stored in user preferences for subsequent cloud API calls
  - **Used in:** html/js/desktop.js (store access token for cloud API calls).

## Updates

- **POST /update/begin**
  - **Description:** Start system update/restore process
  - **Response:** Boolean; triggers update/restore process.
  - **Data Source:** System update mechanism - initiates firmware/OS update procedure  
  - **System Impact:** May restart system services and update MOD OS components
  - **File Operations:** Applies system update packages to MOD device firmware
  - **Used in:** html/js/desktop.js (upgradeWindow.startUpgrade).

- **POST /update/download/**
  - **Description:** Upload system image file for firmware update
  - **Body:** uploaded image file (multipart/binary)
  - **Example:** Binary system image file (.img, .tar.xz, etc.)
  - **Response:** { ok: true, result: true }
  - **Data Source:** Uploaded firmware image validated and staged for installation
  - **File Operations:** Stores uploaded image in temporary location for update process
  - **Security:** Image signature verification and integrity checks performed
  - **Used in:** html/js/upgrade.js (downloadStart) via SimpleTransference.

- **POST /controlchain/download/**
  - **Description:** Upload firmware for Control Chain hardware devices
  - **Body:** uploaded firmware file (binary)
  - **Example:** Binary firmware file (.bin, .hex, etc.) for MOD hardware components
  - **Response:** { ok: true, result: true }
  - **Data Source:** Control Chain device firmware update system
  - **Hardware Operation:** Programs firmware into Control Chain microcontrollers via serial protocol
  - **Device Impact:** Updates knobs, footswitches, displays, and other MOD hardware components
  - **Used in:** html/js/upgrade.js (device firmware update), html/js/desktop.js (cc device manager).

- **POST /controlchain/cancel/**
  - **Description:** Cancel ongoing Control Chain firmware update
  - **Response:** Boolean (true if canceled or noop)
  - **Data Source:** Control Chain update process manager
  - **Hardware Safety:** Safely aborts firmware update to prevent device corruption
  - **Used in:** html/js/desktop.js (cancelDownload in ControlChainDeviceManager).

## Packages (Plugin bundles)

- POST /package/uninstall
  - Request: JSON array of bundle absolute paths to remove.
  - Response: { ok: boolean, removed: [uris], error?: string }
  - Used in: html/js/desktop.js (cloudPluginBox remove bundles).

- **POST /effect/install**
  - **Description:** Install a plugin package from uploaded bundle file
  - **Body:** uploaded tar.gz bundle (binary)
  - **Response:** { ok: boolean, installed: [uris], removed: [uris], error?: string }
  - **Example Response:**
    ```json
    {
      "ok": true,
      "installed": ["http://guitarix.sourceforge.net/plugins/gx_chorus#_chorus"],
      "removed": [],
      "error": null
    }
    ```
  - **Data Source:** Uploaded LV2 bundle validated and installed to system LV2 directories
  - **File Operations:** Extracts tar.gz to appropriate LV2 directory, validates bundle structure
  - **Dependency Handling:** May remove conflicting versions and install new plugin versions
  - **Side Effects:** Websocket `rescan` message sent after successful installation
  - **Used in:** html/js/installation.js (SimpleTransference when installing bundles).

## Static Resources and Templates (Served by Backend)

- **GET /resources/(.*)**
  - **Description:** Serve static UI resources (images, fonts, CSS, JS files)
  - **Example:** `/resources/img/icons/plugin.png`, `/resources/css/main.css`
  - **Data Source:** Filesystem - serves files from `html/resources/` directory
  - **Content Types:** Images (PNG, SVG), stylesheets, JavaScript, fonts
  - **Caching:** Static assets with appropriate cache headers for performance

- **GET /load_template/\<name>.html**
  - **Description:** Serve HTML templates for dynamic UI components
  - **Example:** `/load_template/pedalboard.html`, `/load_template/effect_info.html`
  - **Data Source:** HTML template files from `html/include/` directory
  - **Usage:** Loaded dynamically by frontend JavaScript for UI components
  - **Templates:** Modal dialogs, plugin info panels, settings pages, etc.

- **GET /js/templates.js**
  - **Description:** Serve compiled JavaScript template definitions
  - **Data Source:** Pre-compiled templates from build process or dynamic generation
  - **Content:** JavaScript functions for rendering UI components
  - **Usage:** Template engine support for frontend rendering

## Mismatch note (frontend references without backend route)

- GET /effect/search
  - Referenced in: html/js/desktop.js (cloudPluginSearchFunction). There is no matching route in mod/webserver.py; this code path is effectively unused (local search uses lunr, remote search goes to cloud APIs when enabled).

---

## Data Architecture & Flow

### Core Data Sources

#### LV2 Plugin System
- **Location:** System LV2 directories (e.g., `/usr/lib/lv2/`, `~/.lv2/`)
- **Library:** `lilv` C library for LV2 plugin discovery and introspection
- **Cached in:** `mod/host.py` plugin cache for performance
- **Provides:** Plugin metadata, port information, presets, GUI templates

#### mod-host Audio Engine
- **Protocol:** Custom protocol over Unix sockets (`/tmp/mod-host`)
- **Provides:** Real-time audio processing, parameter changes, connections
- **Messages:** Plugin instantiation, parameter sets, JACK port management

#### Control Chain Hardware
- **Protocol:** Serial communication with MOD hardware devices
- **Location:** `mod/hmi.py`, `mod/addressings.py`
- **Provides:** Physical knobs, footswitches, displays, LEDs
- **Data:** Hardware actuator metadata, addressing mappings, device status

#### JACK Audio System
- **Source:** JACK audio server port discovery
- **Location:** `mod/host.py` JACK client callbacks
- **Provides:** System audio/MIDI ports, connections, buffer size, sample rate

#### File System
- **Pedalboards:** `~/pedalboards/` directory (`.pedalboard` bundle format)
- **Screenshots:** Generated PNG files in pedalboard bundles
- **User Preferences:** `~/.config/mod-ui/preferences.json`
- **Plugin Files:** LV2 bundle resources (GUI templates, stylesheets, etc.)

### Data Flow Patterns

#### Real-time Parameter Changes
1. **User Input:** Hardware knob/frontend slider → `param_set` websocket message
2. **Backend Processing:** `mod/session.py` → `mod/host.py param_set()`  
3. **Audio Engine:** mod-host updates LV2 plugin parameter
4. **Broadcast:** Parameter change sent via websocket to all connected clients
5. **Visual Update:** Frontend updates all GUI representations

#### Plugin Loading
1. **User Action:** Drag plugin from browser → `/effect/add` HTTP request
2. **Backend Processing:** `mod/host.py add_plugin()` → mod-host instantiation
3. **WebSocket Notification:** `add` message with plugin details sent to all clients
4. **GUI Loading:** Frontend requests plugin GUI files via `/effect/file/` endpoints
5. **Visual Rendering:** Plugin appears on pedalboard canvas

#### Hardware Addressing
1. **User Mapping:** Assign parameter to hardware control → `/effect/parameter/address`
2. **Backend Setup:** `mod/addressings.py` creates mapping, configures Control Chain
3. **Hardware Communication:** HMI protocol updates physical device (LEDs, display)
4. **WebSocket Broadcast:** `hw_map` message sent to update all clients
5. **Bidirectional Control:** Hardware changes parameters, parameters update hardware

#### Pedalboard State Management
1. **Loading:** `loading_start` → sequential `add`/`connect`/`param_set` messages → `loading_end`
2. **Saving:** Collect current state → write `.pedalboard` bundle → update file list
3. **Snapshots:** Capture parameter states → `pedal_snapshot` message → restore state
4. **Screenshots:** Render canvas → save PNG → associate with pedalboard

### Message Flow Control
- **Flow Control:** `data_ready` counter system prevents websocket message overflow
- **Event Batching:** Multiple parameter changes batched before sending to frontend
- **Client Sync:** All connected browsers receive identical state via broadcast messages

### Performance Considerations
- **Plugin Cache:** LV2 scanning results cached to avoid repeated filesystem access
- **Screenshot Generation:** Asynchronous rendering to avoid blocking UI operations  
- **Hardware Polling:** Control Chain devices polled efficiently to minimize latency
- **Memory Monitoring:** System stats collected periodically for performance display

---

## Implementation References
- **Backend routes:** `mod/webserver.py` (application = web.Application([...]))
- **Frontend calls:** Search across `html/js/**/*.js` for $.ajax, $.get, new WebSocket, SimpleTransference
- **WebSocket handling:** `mod/session.py` websocket_* methods and `msg_callback()`
- **Audio engine:** `mod/host.py` communicating with mod-host via Unix sockets
- **Hardware control:** `mod/hmi.py` and `mod/addressings.py` for Control Chain protocol

If you need more detail for a specific endpoint (edge cases, timeouts), check the corresponding handler class in `mod/webserver.py`, and the calling code in the referenced JS file.
