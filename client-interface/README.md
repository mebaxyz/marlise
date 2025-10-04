# Client Interface

The client interface provides the web API and user interface for interacting with the Marlise audio system.

## Purpose

The client interface serves as the user-facing layer of the system, providing:

- RESTful HTTP API for plugin and pedalboard management
- WebSocket connections for real-time event updates
- Web-based UI for visual pedalboard editing
- Authentication and session management (if applicable)

## Architecture

**Framework**: FastAPI  
**Language**: Python 3.8+  
**Protocol**: HTTP/HTTPS + WebSocket  
**Default Port**: 8080

## Components

### api/
FastAPI backend service that:
- Exposes REST endpoints for all operations
- Manages WebSocket connections for real-time updates
- Communicates with session manager via ZeroMQ
- Serves static web assets

### web/
Web client application (browser-based):
- Visual pedalboard interface
- Plugin browser and configuration
- Real-time parameter controls
- Connection visualization

## Dependencies

- Python 3.8+
- FastAPI
- Uvicorn (ASGI server)
- ZeroMQ (pyzmq)
- WebSocket support

## Configuration

Environment variables:
- `CLIENT_INTERFACE_PORT`: HTTP server port (default: 8080)

## API Endpoints

See the main documentation for complete API reference. Key endpoints:

### Plugin Management
- `GET /api/plugins/available` - List available plugins
- `POST /api/plugins` - Load a plugin
- `DELETE /api/plugins/{instance_id}` - Unload plugin
- `PATCH /api/plugins/parameters` - Update parameter

### Pedalboard Management
- `GET /api/pedalboards` - List pedalboards
- `POST /api/pedalboards` - Create pedalboard
- `GET /api/pedalboards/{id}` - Get pedalboard
- `PUT /api/pedalboards/{id}` - Update pedalboard
- `DELETE /api/pedalboards/{id}` - Delete pedalboard

### Health & Status
- `GET /health` - Service health check
- `GET /api/session/health` - Session manager health

### WebSocket
- `ws://localhost:8080/ws` - Real-time event stream

## Usage

The client interface is typically started as a standalone service. See the main README for startup instructions.
