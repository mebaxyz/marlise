# Marlise Folder Structure Guide

Quick reference for understanding the repository organization.

## 📁 Top-Level Structure

```
marlise/
├── 🎵 audio-engine/       → Low-level audio processing
├── 🎛️ session-manager/    → High-level orchestration
├── 🌐 client-interface/   → Web API & UI
├── 📜 scripts/            → Start/stop utilities
├── 📚 docs/               → Documentation
├── 🧪 tests/              → Integration tests
└── 📄 README.md           → Project overview
```

## 🎵 Audio Engine

**Location**: `audio-engine/`  
**Purpose**: Real-time audio processing layer

```
audio-engine/
├── mod-host/           → LV2 plugin host (C)
│   ├── src/           → Source code (if building from source)
│   └── mod-host       → Binary
└── modhost-bridge/    → JSON-RPC bridge (C++)
    ├── build/         → Build output
    └── modhost-bridge → Binary
```

**Key Files**:
- `audio-engine/README.md` - Component documentation
- Binary locations may vary; see start scripts for overrides

## 🎛️ Session Manager

**Location**: `session-manager/`  
**Purpose**: Orchestrates plugins, pedalboards, and connections

```
session-manager/
├── src/                      → Python source code
│   ├── session_manager.py   → Main service
│   ├── pedalboard.py        → Pedalboard management
│   ├── plugin_manager.py    → Plugin operations
│   └── zmq_client.py        → ZeroMQ communication
└── start_session_manager.sh → Service launcher
```

**Key Files**:
- `session-manager/README.md` - Component documentation
- `session-manager/src/` - All Python service code

## 🌐 Client Interface

**Location**: `client-interface/`  
**Purpose**: User-facing web API and interface

```
client-interface/
├── api/              → FastAPI backend
│   ├── main.py      → Application entry point
│   ├── routes/      → API endpoint handlers
│   ├── websocket.py → Real-time events
│   └── zmq_client.py → Session manager communication
└── web/             → Web client (HTML/CSS/JS)
    ├── index.html
    ├── css/
    └── js/
```

**Key Files**:
- `client-interface/README.md` - Component documentation
- `client-interface/api/main.py` - FastAPI application

## 📜 Scripts

**Location**: `scripts/`  
**Purpose**: Service management utilities

```
scripts/
├── start-service.sh   → Start all services
├── stop-service.sh    → Stop all services
└── README.md          → Usage instructions
```

**Usage**:
```bash
./scripts/start-service.sh   # Start everything
./scripts/stop-service.sh    # Stop everything
```

## 📚 Documentation

**Location**: `docs/`  
**Purpose**: Technical documentation

```
docs/
├── ARCHITECTURE_OVERVIEW.md        → System architecture
├── COMMUNICATION_ARCHITECTURE.md   → Protocol specs
├── COMMUNICATION_QUICK_REFERENCE.md → API reference
└── COMMUNICATION_FLOW_DIAGRAMS.md   → Sequence diagrams
```

**What to read**:
- New to project? Start with `ARCHITECTURE_OVERVIEW.md`
- Need API details? See `COMMUNICATION_ARCHITECTURE.md`
- Quick lookup? Use `COMMUNICATION_QUICK_REFERENCE.md`

## 🧪 Tests

**Location**: `tests/`  
**Purpose**: Integration and system tests

```
tests/
├── test_zmq_communication.py  → ZeroMQ layer tests
├── test_http_api.py           → HTTP API tests
└── test_api_completeness.py   → API coverage verification
```

**Running tests**:
```bash
python tests/test_zmq_communication.py
python tests/test_http_api.py
```

## 🚫 Ignored Directories (not in git)

These are generated at runtime and git-ignored:

```
logs/       → Service logs (mod-host.log, modhost-bridge.log, etc.)
run/        → PID files for running services
build/      → CMake build artifacts
```

## 📍 Quick Navigation

| I want to... | Go to... |
|-------------|----------|
| Understand architecture | `docs/ARCHITECTURE_OVERVIEW.md` |
| Build audio engine | `audio-engine/mod-host/`, `audio-engine/modhost-bridge/` |
| Develop session logic | `session-manager/src/` |
| Work on web API | `client-interface/api/` |
| Modify web UI | `client-interface/web/` |
| Start/stop services | `scripts/` |
| Run tests | `tests/` |
| Read protocol specs | `docs/COMMUNICATION_ARCHITECTURE.md` |

## 🔧 Environment Variables

Each component uses environment variables for configuration. Check the component READMEs:

- **Audio Engine**: `audio-engine/README.md`
- **Session Manager**: `session-manager/README.md`
- **Client Interface**: `client-interface/README.md`

## 🎯 Design Principles

1. **Self-explanatory names**: Folder names describe their purpose
2. **Layer separation**: Each major folder is an architectural layer
3. **README everywhere**: Every component has documentation
4. **No submodules**: All code is directly in the repository
5. **Clean separation**: Build artifacts are in separate, ignored directories

## 💡 Tips

- Start with the main `README.md` for project overview
- Check component `README.md` files for detailed information
- Use `scripts/` for service management - don't start components manually
- Logs are in `logs/` - check them when troubleshooting
- Build artifacts go in `build/` - this is gitignored
