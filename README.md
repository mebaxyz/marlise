# Marlise

A fork of [MOD-UI](https://github.com/moddevices/mod-ui) from [MOD-AUDIO](https://modaudio.com/), enhanced and customized for specific use cases.

## About

This project is based on the MOD-UI interface, which is the web-based user interface for MOD audio devices. MOD-UI provides a visual pedalboard interface for connecting audio effects and instruments in real-time.

### Original Project

- **Original Repository**: [MOD-UI by MOD Audio](https://github.com/moddevices/mod-ui)
- **MOD Audio Website**: https://modaudio.com/
- **Documentation**: https://wiki.modaudio.com/

## Project Structure

This project follows a clear, self-explanatory folder structure:

```
marlise/
├── audio-engine/          # Low-level audio processing
│   ├── mod-host/         # LV2 plugin host (C)
│   └── modhost-bridge/   # JSON-RPC to text protocol bridge (C++)
├── session-manager/       # High-level session management (Python)
│   └── src/              # Session manager source code
├── client-interface/      # Web API and UI (FastAPI)
│   ├── api/              # FastAPI backend
│   └── web/              # Web client
├── scripts/               # Start/stop scripts
├── docs/                  # Complete documentation
├── tests/                 # Integration tests
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mebaxyz/marlise.git
cd marlise
```

2. Build the components (instructions for each component in their respective directories)

## Architecture

This project uses a simplified, high-performance architecture with direct ZeroMQ communication, organized into three self-explanatory layers:

### 🎵 Audio Engine (`audio-engine/`)
Low-level audio processing layer:
- **mod-host**: LV2 plugin host for audio processing
- **modhost-bridge**: C++ bridge translating JSON-RPC to mod-host text protocol

### 🎛️ Session Manager (`session-manager/`)
High-level orchestration layer:
- Python service managing plugins, pedalboards, and audio connections
- Maintains session state and provides persistence

### 🌐 Client Interface (`client-interface/`)
User-facing layer:
- FastAPI web service for REST API
- WebSocket support for real-time updates
- Web-based UI for visual pedalboard editing

## Documentation

📚 **Complete Documentation** (in `docs/` folder):
- [**Communication Architecture**](docs/COMMUNICATION_ARCHITECTURE.md) - Complete technical documentation
- [**Quick Reference**](docs/COMMUNICATION_QUICK_REFERENCE.md) - Developer quick reference  
- [**Flow Diagrams**](docs/COMMUNICATION_FLOW_DIAGRAMS.md) - Visual sequence diagrams

📂 **Component Documentation**:
- [Audio Engine](audio-engine/README.md) - Low-level audio processing
- [Session Manager](session-manager/README.md) - High-level orchestration
- [Client Interface](client-interface/README.md) - Web API and UI

## Usage

### Quick Start

1. **Start all services**:
```bash
./scripts/start-service.sh
```

2. **Open web interface**:
```bash
# Browser: http://localhost:8080
```

3. **Test communication**:
```bash
python3 tests/test_zmq_communication.py
```

4. **Stop services**:
```bash  
./scripts/stop-service.sh
```

### API Examples

```bash
# Get available plugins
curl http://localhost:8080/api/plugins/available

# Load a plugin
curl -X POST http://localhost:8080/api/plugins \
  -H "Content-Type: application/json" \
  -d '{"uri": "http://calf.sourceforge.net/plugins/Reverb"}'

# Update parameter
curl -X PATCH http://localhost:8080/api/plugins/parameters \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "1", "port": "gain", "value": 0.5}'
```

## Development

### API Integration Status ✅

**All FastAPI client API endpoints are now fully integrated with the session manager ZMQ handlers!**

#### ✅ Fully Integrated Routers (35+ endpoints):

- **Snapshots** (7 endpoints): save, save_as, rename, remove, list, get_name, load
- **Favorites** (2 endpoints): add, remove  
- **Recording** (7 endpoints): start, stop, start_playback, wait_playback, stop_playback, download, reset
- **Updates** (5 endpoints): begin_update, upload_system_image, upload_controlchain_firmware, cancel_controlchain_update, uninstall_package
- **JACK** (2 endpoints): get_midi_devices, set_midi_device
- **Banks** (2 endpoints): get_banks, save_banks
- **Files** (1 endpoint): list_user_files
- **Auth** (2 endpoints): handle_auth_nonce, handle_auth_token
- **Pedalboards** (multiple endpoints): save, load, list, pack_bundle, factory_copy, info, remove, image operations
- **Plugins** (multiple endpoints): list, bulk, get, add, remove, connect, disconnect, parameter operations, presets
- **System** (multiple endpoints): ping, reset, buffer_size, true_bypass, config operations

#### ❌ Remaining (misc.py - 6 endpoints):
- `/ping` - Simple ping endpoint
- `/hello` - Hello endpoint (placeholder)
- `/save_user_id` - Store user identity
- `/resources/{path:path}` - Static UI resources
- `/load_template/{name}.html` - HTML templates
- `/js/templates.js` - JavaScript templates

#### 🔧 Integration Features:
- ✅ Proper ZMQ client calls with configurable timeouts (3-30 seconds)
- ✅ Structured error responses with success/failure status
- ✅ Parameter validation and logging
- ✅ Async/await patterns throughout
- ✅ Modular handler architecture (separate files by functionality)
- ✅ Removed duplicate/fake session-manager directory

### Prerequisites

- **Python 3.8+** with asyncio support
- **ZeroMQ** library (`libzmq`)  
- **JACK Audio** (or PipeWire with pw-jack)
- **LV2 plugins** (e.g., Calf, LSP, etc.)
- **FastAPI** and dependencies (see requirements.txt)

### Architecture Benefits

✅ **Direct ZeroMQ Communication** - No Redis dependency  
✅ **High Performance** - Microsecond-level messaging  
✅ **Simplified Stack** - Removed ServiceBus complexity  
✅ **Real-time Events** - WebSocket + ZeroMQ pub/sub  
✅ **Clean APIs** - RESTful HTTP + JSON-RPC

## Contributing

[Add contributing guidelines if applicable]

## Acknowledgments

- **MOD Audio Team** for creating the original MOD-UI
- **MOD Community** for their continuous contributions
- All contributors to the MOD ecosystem

## Support

[Add support information or links here]

---

## License

This project is inspired by and builds upon concepts from MOD-UI, and is distributed under the GNU Affero General Public License v3 (AGPL-3.0). See the `LICENSE` file for the full license text.

### Attribution

This project is inspired by the MOD-UI interface and MOD Audio ecosystem:

- Original MOD-UI repository: https://github.com/moddevices/mod-ui
- MOD Audio: https://modaudio.com/
- MOD Audio documentation: https://wiki.modaudio.com/

We are grateful to the MOD Audio team and community for their pioneering work in creating an open-source audio plugin host and interface.