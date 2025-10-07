# Session Manager Configuration

This document describes all configuration options for the Session Manager service, including environment variables, ports, and runtime settings.

## Environment Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODHOST_BRIDGE_ENDPOINT` | `tcp://127.0.0.1:6000` | ZeroMQ endpoint for modhost-bridge service |
| `MODHOST_BRIDGE_TIMEOUT` | `5.0` | Timeout in seconds for bridge calls |
| `BRIDGE_CONNECT_RETRIES` | `5` | Number of connection retry attempts |
| `BRIDGE_CONNECT_RETRY_DELAY` | `1.0` | Delay in seconds between retry attempts |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_MANAGER_AUTO_CREATE_DEFAULT` | `0` | Auto-create default pedalboard on startup (1=true, 0=false) |

### Logging and Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | Standard | Log message format |

## Port Configuration

The Session Manager uses dynamically assigned ports based on a hash of the service name to avoid conflicts:

### Port Calculation

```python
service_hash = zlib.crc32(service_name.encode("utf-8")) % 1000
rpc_port = base_port + service_hash          # ~5718
pub_port = base_port + service_hash + 1000   # ~6718
sub_port = base_port + service_hash + 2000   # ~7718
```

### Default Ports

- **RPC Port**: 5718 (handles incoming method calls)
- **PUB Port**: 6718 (publishes events)
- **SUB Port**: 7718 (subscribes to events)

### Port Ranges

- Base port: 5555 (configurable in ZMQService constructor)
- RPC range: 5555-6555
- PUB range: 6555-7555
- SUB range: 7555-8555

## Runtime Configuration

### JACK Audio System

The service integrates with JACK Audio Connection Kit for low-latency audio processing.

#### JACK Configuration

| Parameter | Description | Configurable |
|-----------|-------------|--------------|
| Buffer Size | Audio buffer size in frames | Yes |
| Sample Rate | Audio sample rate in Hz | Read-only |
| Hardware Ports | Available audio interfaces | Read-only |

#### JACK Environment Variables

```bash
# Force JACK usage (if PipeWire is present)
export JACK_NO_AUDIO_RESERVATION=1

# Set JACK buffer size
export JACK_BUFFER_SIZE=1024

# Enable JACK debugging
export JACK_LOG_LEVEL=debug
```

### LV2 Plugin System

#### Plugin Discovery

Plugins are discovered through the LV2_PATH environment variable:

```bash
export LV2_PATH=/usr/lib/lv2:/usr/local/lib/lv2:$HOME/.lv2
```

#### Plugin Categories

The service supports all standard LV2 plugin types:
- Generators
- Effects
- Instruments
- Utilities

## Service Dependencies

### Required Services

1. **modhost-bridge** (C++ service)
   - Endpoint: Configurable via `MODHOST_BRIDGE_ENDPOINT`
   - Protocol: ZeroMQ JSON-RPC
   - Timeout: Configurable via `MODHOST_BRIDGE_TIMEOUT`

2. **mod-host** (LV2 host)
   - Communicates via modhost-bridge
   - Requires JACK or PipeWire

### Optional Services

1. **Client Interface** (FastAPI)
   - Connects to Session Manager via ZeroMQ
   - Provides web API and UI

## Configuration Files

### Pedalboard Storage

Pedalboards are stored as JSON files in the configured storage directory:

```json
{
  "name": "My Pedalboard",
  "description": "A custom effects chain",
  "plugins": [...],
  "connections": [...],
  "snapshots": [...]
}
```

### Plugin Metadata

Plugin information is cached from the bridge service:

```json
{
  "uri": "http://example.com/plugin",
  "name": "Example Plugin",
  "brand": "Example Corp",
  "version": "1.0.0",
  "ports": {...},
  "parameters": [...]
}
```

## Security Configuration

### Network Security

- All communication uses localhost-only ZeroMQ sockets
- No authentication or encryption (localhost assumption)
- Firewall should restrict external access to ZMQ ports

### Process Security

- Runs as unprivileged user
- Requires access to audio devices (JACK group)
- LV2 plugin loading may require additional permissions

## Monitoring and Observability

### Health Checks

The service provides health check endpoints:

```python
# Via ZeroMQ RPC
await zmq_client.call("session_manager", "health_check")

# Via HTTP (through client interface)
GET /health
```

### Metrics

Available metrics include:
- Active plugin instances
- Current pedalboard state
- Connection count
- CPU usage (via mod-host)
- Memory usage

### Logging

Structured logging with configurable levels:

```python
logger.info("Service started on port %d", port)
logger.debug("Plugin loaded: %s", instance_id)
logger.error("Bridge communication failed: %s", error)
```

## Troubleshooting Configuration

### Common Configuration Issues

1. **Bridge Connection Failed**
   ```bash
   # Check if bridge is running
   netstat -tlnp | grep 6000

   # Test connectivity
   telnet localhost 6000
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :5718

   # Change base port
   export ZMQ_BASE_PORT=6000
   ```

3. **Plugin Discovery Issues**
   ```bash
   # Check LV2 path
   echo $LV2_PATH

   # List available plugins
   lv2ls
   ```

### Debug Configuration

Enable verbose logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export MODHOST_BRIDGE_TIMEOUT=10.0
export BRIDGE_CONNECT_RETRIES=10
```

## Advanced Configuration

### Custom Bridge Client

For specialized deployments, the bridge client can be customized:

```python
class CustomBridgeClient(BridgeClient):
    async def call(self, service_name, method, **kwargs):
        # Custom logic here
        return await super().call(service_name, method, **kwargs)
```

### Plugin Validation

Custom plugin validation can be added:

```python
async def validate_plugin(plugin_uri: str) -> bool:
    # Custom validation logic
    return True
```

### Event Filtering

Event publishing can be filtered or enhanced:

```python
async def publish_event(event_type: str, data: dict):
    # Add custom metadata
    data['timestamp'] = datetime.now().isoformat()
    await zmq_service.publish_event(event_type, data)
```