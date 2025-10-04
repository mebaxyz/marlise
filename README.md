# Marlise

A fork of [MOD-UI](https://github.com/moddevices/mod-ui) from [MOD-AUDIO](https://modaudio.com/), enhanced and customized for specific use cases.

## About

This project is based on the MOD-UI interface, which is the web-based user interface for MOD audio devices. MOD-UI provides a visual pedalboard interface for connecting audio effects and instruments in real-time.

### Original Project

- **Original Repository**: [MOD-UI by MOD Audio](https://github.com/moddevices/mod-ui)
- **MOD Audio Website**: https://modaudio.com/
- **Documentation**: https://wiki.modaudio.com/

## Submodules

This project includes the following submodules:

- **mod-ui**: Fork of the original MOD-UI interface (feature/fastapi-migration branch)
- **mado-audio-host**: Audio host component for enhanced functionality

## Installation

1. Clone the repository with submodules:
```bash
git clone --recursive https://github.com/mebaxyz/marlise.git
cd marlise
```

2. If you've already cloned without submodules, initialize them:
```bash
git submodule init
git submodule update
```

## Architecture

This project uses a simplified, high-performance architecture with direct ZeroMQ communication:

- **mod-host**: LV2 plugin host (audio processing)
- **modhost-bridge**: C++ service bridging JSON-RPC to mod-host text protocol  
- **session-manager**: Python service managing high-level operations
- **client-interface**: FastAPI web service for browser interaction

## Documentation

📚 **Complete Communication Documentation**:
- [**Communication Architecture**](COMMUNICATION_ARCHITECTURE.md) - Complete technical documentation
- [**Quick Reference**](COMMUNICATION_QUICK_REFERENCE.md) - Developer quick reference  
- [**Flow Diagrams**](COMMUNICATION_FLOW_DIAGRAMS.md) - Visual sequence diagrams

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
python3 test_zmq_communication.py
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

This project is a fork of MOD-UI and is distributed under the GNU Affero General Public License v3 (AGPL-3.0). See the top-level `LICENSE` file for the full license text.

The `mod-ui` submodule included in this repository is also licensed under the AGPLv3; its original license file is kept in `mod-ui/LICENSE`.

### Attribution

This fork builds on work from the MOD-UI project. Original project:

- MOD-UI repository: https://github.com/moddevices/mod-ui
- MOD Audio: https://modaudio.com/

If you are the copyright holder and want a different license or explicit copyright line in
the top-level `LICENSE`, please update the `LICENSE` file accordingly.