# Audio Engine

The audio engine layer is responsible for low-level audio processing and LV2 plugin hosting.

## Components

### mod-host
- **Purpose**: LV2 plugin host for audio processing
- **Language**: C
- **Protocol**: TCP Socket (text-based commands)
- **Default Port**: 5555

The mod-host binary loads and manages LV2 audio plugins, handles JACK audio connections, and provides a simple text-based command interface.

### modhost-bridge
- **Purpose**: Bridge service that translates JSON-RPC to mod-host text protocol
- **Language**: C++
- **Protocol**: ZeroMQ (REQ/REP) for JSON-RPC
- **Default Port**: 6000

The modhost-bridge acts as a translation layer, converting JSON-RPC requests from the session manager into the text commands that mod-host understands.

## Building

Instructions for building mod-host and modhost-bridge will be added here.

## Configuration

Environment variables:
- `MOD_HOST_PORT`: TCP port for mod-host (default: 5555)
- `MOD_HOST_FEEDBACK_PORT`: Feedback port (default: 5556)
- `MODHOST_BRIDGE_ENDPOINT`: ZeroMQ endpoint (default: tcp://127.0.0.1:6000)

## Usage

The audio engine components are typically started via the scripts in the `scripts/` directory at the repository root.
