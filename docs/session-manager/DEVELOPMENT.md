# Session Manager Development Guide

This guide covers development setup, testing, debugging, and contribution guidelines for the Session Manager service.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- ZeroMQ development libraries
- JACK Audio Connection Kit or PipeWire
- LV2 plugin packages

### Installation

```bash
# Clone repository
git clone https://github.com/mebaxyz/marlise.git
cd marlise/session-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Required Dependencies

**Core Dependencies:**
- `pyzmq`: ZeroMQ Python bindings
- `asyncio`: Built-in async support

**Development Dependencies:**
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `pytest-mock`: Mocking utilities
- `black`: Code formatting
- `isort`: Import sorting
- `flake8`: Linting
- `mypy`: Type checking

## Project Structure

```
session-manager/
├── main.py                 # Service entry point
├── core/                   # Core business logic
│   ├── plugin_manager.py   # Plugin lifecycle management
│   ├── session_manager.py  # Session coordination
│   ├── bridge_client.py    # Bridge communication
│   ├── pedalboard_service.py
│   ├── connection_service.py
│   └── session_control_service.py
├── handlers/               # RPC method handlers
│   └── zmq_handlers.py     # ZeroMQ RPC handlers
├── zmq_service.py          # ZeroMQ service implementation
├── tests/                  # Test suite
│   ├── conftest.py         # Test configuration
│   ├── test_*.py           # Unit tests
│   └── integration/        # Integration tests
└── requirements*.txt       # Dependencies
```

## Running the Service

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run service
python -m session-manager.main

# Or with debug logging
LOG_LEVEL=DEBUG python -m session-manager.main
```

### With Dependencies

The Session Manager requires the modhost-bridge service to be running:

```bash
# Terminal 1: Start modhost-bridge
./scripts/start-modhost-bridge.sh

# Terminal 2: Start session manager
python -m session-manager.main

# Terminal 3: Test connectivity
python tests/test_zmq_communication.py
```

## Testing

### Unit Tests

Run unit tests with pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_plugin_manager.py

# Run with coverage
pytest --cov=session_manager --cov-report=html

# Run async tests
pytest -k "async" --asyncio-mode=auto
```

### Integration Tests

```bash
# Run integration tests (requires full stack)
pytest tests/integration/

# Run with service dependencies
docker-compose -f docker/docker-compose.test.yml up -d
pytest tests/integration/test_full_workflow.py
```

### Test Structure

**Unit Tests:**
- Test individual components in isolation
- Mock external dependencies (bridge, ZMQ)
- Focus on business logic and error handling

**Integration Tests:**
- Test component interaction
- Require running services
- Validate end-to-end workflows

### Writing Tests

```python
import pytest
from session_manager.core.plugin_manager import PluginManager

class TestPluginManager:
    @pytest.mark.asyncio
    async def test_load_plugin_success(self, mock_bridge_client):
        manager = PluginManager(mock_bridge_client, None)

        # Test successful plugin loading
        result = await manager.load_plugin("http://example.com/plugin")

        assert "instance_id" in result
        assert result["plugin"]["uri"] == "http://example.com/plugin"
```

## Debugging

### Logging

Enable detailed logging:

```bash
# Debug level
export LOG_LEVEL=DEBUG

# Structured logging
export LOG_FORMAT=json

# Log to file
python -m session-manager.main 2>&1 | tee session-manager.log
```

### ZeroMQ Debugging

Monitor ZeroMQ traffic:

```bash
# Install zmq tools
pip install zmq-tools

# Monitor RPC calls
zmq-proxy tcp://127.0.0.1:5718 tcp://127.0.0.1:6718

# Debug connection issues
netstat -tlnp | grep 57
```

### Bridge Communication

Debug bridge communication:

```bash
# Test bridge connectivity
telnet localhost 6000

# Monitor bridge logs
tail -f logs/modhost-bridge.log

# Test bridge methods
python3 -c "
import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect('tcp://127.0.0.1:6000')
sock.send_json({'action': 'audio', 'method': 'get_jack_sample_rate'})
print(sock.recv_json())
"
```

### Audio System Debugging

Debug JACK/PipeWire issues:

```bash
# Check JACK status
jackd -S

# List JACK ports
jack_lsp

# Monitor JACK connections
jack_connect system:capture_1 plugin:input_1
```

## Code Quality

### Linting and Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy .
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Code Standards

**Python Style:**
- Follow PEP 8
- Use type hints
- Maximum line length: 120 characters
- Use f-strings for formatting

**Async Code:**
- Use `async`/`await` consistently
- Avoid blocking operations in async functions
- Use `asyncio.Lock` for shared state

**Error Handling:**
- Use specific exception types
- Log errors with context
- Return structured error responses

## Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write Tests First**
   ```bash
   # Add tests for new functionality
   pytest tests/test_my_feature.py
   ```

3. **Implement Feature**
   ```bash
   # Write code following established patterns
   # Update documentation
   ```

4. **Run Full Test Suite**
   ```bash
   pytest --cov=session_manager
   flake8 .
   mypy .
   ```

5. **Submit Pull Request**
   ```bash
   git push origin feature/my-feature
   # Create PR with description
   ```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: What, why, and how
- **Tests**: Include tests for new functionality
- **Documentation**: Update docs for API changes
- **Breaking Changes**: Clearly mark breaking changes

### Commit Messages

Follow conventional commits:

```
feat: add plugin preset management
fix: resolve ZeroMQ timeout in bridge client
docs: update API reference for new methods
test: add integration tests for pedalboard loading
refactor: simplify connection service logic
```

## Performance Optimization

### Profiling

```bash
# Profile service startup
python -m cProfile -s time session-manager/main.py

# Profile specific operations
import cProfile
cProfile.run('asyncio.run(test_operation())')
```

### Memory Usage

Monitor memory usage:

```bash
# Use memory_profiler
pip install memory-profiler
python -m memory_profiler session-manager/main.py
```

### Async Performance

- Use `asyncio.gather()` for concurrent operations
- Avoid blocking I/O in async functions
- Use connection pooling for ZeroMQ

## Troubleshooting Development Issues

### Common Problems

1. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"

   # Install missing dependencies
   pip install -r requirements.txt
   ```

2. **ZeroMQ Connection Refused**
   ```bash
   # Check if ports are bound
   netstat -tlnp | grep 57

   # Kill conflicting processes
   pkill -f zmq
   ```

3. **Plugin Loading Failures**
   ```bash
   # Check LV2_PATH
   echo $LV2_PATH

   # List available plugins
   lv2ls | head -10
   ```

4. **Async Test Failures**
   ```bash
   # Use correct asyncio mode
   pytest --asyncio-mode=auto

   # Check for event loop conflicts
   pytest -s --tb=long
   ```

### Getting Help

- **Logs**: Check service logs in `logs/` directory
- **Tests**: Run tests with verbose output
- **Documentation**: Refer to project docs
- **Issues**: Create GitHub issue with reproduction steps

## Advanced Development

### Custom Bridge Clients

```python
class CustomBridgeClient(BridgeClient):
    async def call(self, service_name, method, **kwargs):
        # Add custom logic, monitoring, etc.
        start_time = time.time()
        result = await super().call(service_name, method, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Bridge call {method} took {duration:.3f}s")
        return result
```

### Plugin Extensions

```python
class CustomPluginManager(PluginManager):
    async def validate_plugin(self, uri: str) -> bool:
        # Custom validation logic
        return await super().validate_plugin(uri)
```

### Event System Extensions

```python
class CustomZMQService(ZMQService):
    async def publish_event(self, event_type: str, data: dict):
        # Add custom event processing
        data['timestamp'] = datetime.now().isoformat()
        await super().publish_event(event_type, data)
```

## Deployment

### Production Setup

```bash
# Install system dependencies
sudo apt install python3 python3-pip libzmq3-dev jackd2

# Create system user
sudo useradd -r -s /bin/false session-manager

# Install application
sudo pip3 install -r requirements.txt

# Configure systemd service
sudo cp scripts/session-manager.service /etc/systemd/system/
sudo systemctl enable session-manager
sudo systemctl start session-manager
```

### Docker Development

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements*.txt ./
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "session-manager.main"]
```

### Monitoring

Set up monitoring for production:

```python
# Add metrics collection
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

@zmq_handler
async def monitored_method(**kwargs):
    with REQUEST_LATENCY.time():
        REQUEST_COUNT.labels(method='monitored_method').inc()
        return await actual_method(**kwargs)
```