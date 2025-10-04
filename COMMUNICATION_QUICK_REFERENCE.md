# Communication Quick Reference

## Service Endpoints

```bash
# Client Interface (Web API)
http://localhost:8080/health
ws://localhost:8080/ws

# Session Manager (ZeroMQ)
tcp://127.0.0.1:5718  # RPC
tcp://127.0.0.1:6718  # PUB  
tcp://127.0.0.1:7718  # SUB

# Modhost Bridge (ZeroMQ)
tcp://127.0.0.1:6000

# mod-host (TCP)
tcp://127.0.0.1:5555
```

## Common API Calls

### Load a Plugin
```bash
# HTTP API
curl -X POST http://localhost:8080/api/plugins \
  -H "Content-Type: application/json" \
  -d '{"uri": "http://calf.sourceforge.net/plugins/Reverb"}'

# ZeroMQ (Python)
result = await zmq_client.call("session_manager", "load_plugin", 
                               uri="http://calf.sourceforge.net/plugins/Reverb")

# mod-host direct
echo "add http://calf.sourceforge.net/plugins/Reverb 0" | nc localhost 5555
```

### Set Parameter  
```bash
# HTTP API
curl -X PATCH http://localhost:8080/api/plugins/parameters \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "1", "port": "gain", "value": 0.5}'

# ZeroMQ (Python)  
result = await zmq_client.call("session_manager", "set_parameter",
                               instance_id="1", port="gain", value=0.5)

# mod-host direct
echo "param_set 0 gain 0.5" | nc localhost 5555
```

## Message Examples

### ZeroMQ RPC Request
```json
{
  "method": "load_plugin",
  "params": {"uri": "http://plugin.uri"},
  "source_service": "client_interface",
  "request_id": "abc-123",
  "timestamp": "2025-10-04T10:30:00Z"
}
```

### WebSocket Event
```json
{
  "event": "plugin_loaded",
  "data": {"instance_id": "1", "uri": "http://plugin.uri"},
  "timestamp": 1696435200
}
```

### mod-host Command
```
add http://calf.sourceforge.net/plugins/Reverb 0
connect system:capture_1 effect_0:in  
param_set 0 gain 0.8
```

## Testing Commands

```bash
# Test services
./scripts/start-service.sh
python3 test_zmq_communication.py

# Test HTTP API
curl http://localhost:8080/health

# Test WebSocket  
wscat -c ws://localhost:8080/ws

# Test mod-host direct
telnet localhost 5555
```