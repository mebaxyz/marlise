# Session Manager

The session manager is a Python service that manages high-level operations, orchestrating plugins, pedalboards, and audio connections.

## Purpose

The session manager acts as the central orchestration layer, sitting between the client interface and the audio engine. It:

- Manages plugin lifecycle (loading, unloading, parameter updates)
- Handles pedalboard state (creating, saving, loading)
- Coordinates audio connections between plugins
- Maintains session state and provides persistence
- Translates high-level requests into low-level audio engine operations

## Architecture

**Language**: Python 3.8+  
**Protocols**: 
- ZeroMQ REQ/REP for RPC (to client-interface)
- ZeroMQ PUB/SUB for events
- ZeroMQ REQ client (to modhost-bridge)

**Default Ports**:
- RPC Server: 5718 (calculated from service name hash)
- PUB (events): 6718
- SUB (listen): 7718

## Components

### src/
Python source code for the session manager service.

## Dependencies

- Python 3.8+
- ZeroMQ (pyzmq)
- asyncio

## Configuration

Environment variables:
- `SESSION_MANAGER_AUTO_CREATE_DEFAULT`: Auto-create default pedalboard (default: 1)
- `BRIDGE_CONNECT_RETRIES`: Connection retry attempts (default: 5)
- `BRIDGE_CONNECT_RETRY_DELAY`: Delay between retries in seconds (default: 1.0)

## Usage

The session manager is typically started via the scripts in the `scripts/` directory at the repository root.

## API

The session manager exposes JSON-RPC methods for:
- Plugin management (load, unload, set parameters)
- Pedalboard management (create, save, load, list)
- Connection management (connect/disconnect audio ports)
- System operations (health check, CPU load)

See the main documentation for complete API details.
