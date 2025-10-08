# Marlise Web Interface Development Setup

This directory contains the Docker-based development environment for the Marlise web interfaces, providing hot-reload capabilities without requiring image rebuilds.

## Architecture

```
┌─────────────────────────────────────────┐
│ Browser                                 │
└─────────────────┬───────────────────────┘
                  │ HTTP
                  ▼
┌─────────────────────────────────────────┐
│ Tornado Web Client (port 8888)         │
│ - Template serving                      │
│ - Static files                          │
│ - Integrated API proxy                  │
│ - WebSocket proxy                       │
└─────────────────┬───────────────────────┘
                  │ HTTP/WS Proxy
                  ▼
┌─────────────────────────────────────────┐
│ FastAPI Client Interface (port 8080)    │
│ - REST API endpoints                    │
│ - WebSocket handlers                    │
│ - ZeroMQ communication                  │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Start Development Environment
```bash
# Build and start all services
./dev-env.sh start

# Or manually with docker compose
docker compose -f docker-compose.dev.yml up --build -d
```

### 2. Access Services
- **🌐 Web UI**: http://localhost:8888 (Tornado + templates)
- **🔧 API Direct**: http://localhost:8080 (FastAPI)
- **📊 API Documentation**: http://localhost:8080/docs

### 3. Development Workflow
```bash
# Check service status
./dev-env.sh status

# View logs (all services)
./dev-env.sh logs

# View logs (specific service)
./dev-env.sh logs tornado-web-client
./dev-env.sh logs fastapi-client-interface

# Restart services (e.g., after config changes)
./dev-env.sh restart

# Stop services
./dev-env.sh stop
```

## Development Features

### 🔄 Hot Reload
- **Source code is bind-mounted** - changes are immediately visible
- **No image rebuilds needed** for code changes
- **Dependencies pre-installed** in images for fast startup

### 📁 File Structure
```
client-interface/
├── web_client_original/          # Tornado Web Client
│   ├── Dockerfile               # Build with tornado + requests
│   ├── requirements.txt         # Python dependencies
│   ├── standalone_template_server.py # Main server with proxy
│   └── html/                    # Templates and static files
└── web_api/api/                 # FastAPI Client Interface
    ├── Dockerfile               # Build with FastAPI + ZeroMQ
    ├── requirements.txt         # Python dependencies
    └── api/                     # FastAPI application
```

### 🚀 Services

#### Tornado Web Client (`tornado-web-client`)
- **Port**: 8888
- **Purpose**: Serves original UI with server-side templates
- **Features**:
  - Template rendering (Tornado templates)
  - Static file serving (CSS, JS, images)
  - Integrated HTTP API proxy to FastAPI
  - WebSocket proxy (`/websocket` → `/ws`)
- **Bind Mount**: `./client-interface/web_client_original:/app`

#### FastAPI Client Interface (`fastapi-client-interface`)
- **Port**: 8080
- **Purpose**: Modern REST API and WebSocket interface
- **Features**:
  - REST API endpoints (`/api/*`)
  - WebSocket handlers (`/ws`)
  - ZeroMQ communication with session manager
- **Bind Mount**: `./client-interface/web_api/api:/app/api`

## Development Commands

### Environment Management
```bash
./dev-env.sh build      # Build images
./dev-env.sh start      # Start services
./dev-env.sh stop       # Stop services  
./dev-env.sh restart    # Restart services
./dev-env.sh status     # Check health
./dev-env.sh cleanup    # Remove everything
```

### Debugging
```bash
# View all logs in real-time
./dev-env.sh logs

# View specific service logs
./dev-env.sh logs tornado-web-client
./dev-env.sh logs fastapi-client-interface

# Check service health
curl http://localhost:8888/css/dashboard.css  # Static files
curl http://localhost:8080/health             # FastAPI health
curl http://localhost:8888/api/health         # Proxy test
```

### Manual Docker Commands
```bash
# Build specific service
docker compose -f docker-compose.dev.yml build tornado-web-client

# Start specific service
docker compose -f docker-compose.dev.yml up tornado-web-client

# Execute commands in running container
docker compose -f docker-compose.dev.yml exec tornado-web-client bash
docker compose -f docker-compose.dev.yml exec fastapi-client-interface bash

# View container logs
docker compose -f docker-compose.dev.yml logs -f tornado-web-client
```

## API Proxy Testing

The Tornado server includes an integrated proxy that forwards API calls to FastAPI:

```bash
# These are equivalent:
curl http://localhost:8888/api/health    # Via proxy
curl http://localhost:8080/api/health    # Direct FastAPI

# Legacy routes are automatically prefixed:
curl http://localhost:8888/plugins       # → http://localhost:8080/api/plugins
curl http://localhost:8888/pedalboard    # → http://localhost:8080/api/pedalboard
```

## WebSocket Proxy Testing

```bash
# WebSocket connections are proxied:
# ws://localhost:8888/websocket → ws://localhost:8080/ws

# Test with wscat (npm install -g wscat)
wscat -c ws://localhost:8888/websocket
wscat -c ws://localhost:8080/ws  # Direct connection
```

## Troubleshooting

### Port Conflicts
```bash
# Check if ports are in use
netstat -tuln | grep :8888
netstat -tuln | grep :8080

# Stop conflicting services
sudo lsof -i :8888
sudo lsof -i :8080
```

### Service Issues
```bash
# Check Docker status
docker compose -f docker-compose.dev.yml ps

# Restart specific service
docker compose -f docker-compose.dev.yml restart tornado-web-client

# Rebuild if dependencies changed
docker compose -f docker-compose.dev.yml build --no-cache
```

### Health Check Failures
```bash
# Manual health checks
./dev-env.sh status

# Check individual services
curl -f http://localhost:8888/css/dashboard.css || echo "Tornado failed"
curl -f http://localhost:8080/health || echo "FastAPI failed"
```

## Integration with Marlise Backend

To connect with the full Marlise system:

1. **Session Manager**: Start session manager service
2. **Audio Engine**: Start mod-host and modhost-bridge  
3. **Environment Variables**: Set `CLIENT_INTERFACE_ZMQ_HOST` for ZeroMQ connections

```bash
# Example: Connect to host session manager
docker compose -f docker-compose.dev.yml up -d
# Session manager should be running on host:5718 (ZMQ RPC)
```

## Performance Notes

- **Fast startup**: Dependencies pre-installed in images (~10s vs ~60s)
- **Hot reload**: Code changes visible immediately
- **Resource usage**: ~200MB RAM per service
- **Network**: Bridge network for inter-service communication

## Security Considerations

- **Development only**: This setup is for development, not production
- **Bind mounts**: Source code is writable from containers
- **No authentication**: Services run without authentication
- **Network**: Services exposed on host network for testing