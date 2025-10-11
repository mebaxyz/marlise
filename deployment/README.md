# Marlise Deployment

This directory contains deployment configurations and scripts for production use of Marlise on embedded devices (Raspberry Pi) or Linux servers.

## Contents

### Systemd Service Units

Production-grade service management with automatic restart and monitoring:

- **`systemd/marlise-mod-host@.service`** - LV2 plugin host (audio engine)
- **`systemd/marlise-bridge@.service`** - JSON-RPC bridge to mod-host
- **`systemd/marlise-session-manager@.service`** - High-level orchestration service
- **`systemd/marlise-client-interface@.service`** - FastAPI HTTP/WebSocket API
- **`systemd/marlise-web-client@.service`** - Tornado template server
- **`systemd/marlise.target`** - Systemd target to manage all services as a group

### Installation Script

- **`install-systemd.sh`** - Automated installation of systemd units

## Quick Start

### 1. Install Services

```bash
# Install for current user
cd deployment
sudo ./install-systemd.sh

# Or install for specific user
sudo ./install-systemd.sh pi
```

### 2. Start Services

```bash
# Start all Marlise services
sudo systemctl start marlise.target

# Check status
systemctl status 'marlise-*@pi.service'

# View live logs
journalctl -f -u 'marlise-*@pi.service'
```

### 3. Enable Auto-Start on Boot

```bash
sudo systemctl enable marlise.target
```

## Service Management

### Start/Stop Individual Services

```bash
# Replace 'pi' with your username
sudo systemctl start marlise-mod-host@pi.service
sudo systemctl start marlise-bridge@pi.service
sudo systemctl start marlise-session-manager@pi.service
sudo systemctl start marlise-client-interface@pi.service
sudo systemctl start marlise-web-client@pi.service

# Stop services
sudo systemctl stop marlise-mod-host@pi.service
# ... etc
```

### Check Service Status

```bash
# All Marlise services
systemctl status 'marlise-*@pi.service'

# Individual service
systemctl status marlise-session-manager@pi.service
```

### View Logs

```bash
# All services, live tail
journalctl -f -u 'marlise-*@pi.service'

# Specific service
journalctl -u marlise-session-manager@pi.service

# Last 100 lines
journalctl -u marlise-session-manager@pi.service -n 100

# Since last boot
journalctl -u marlise-session-manager@pi.service -b
```

### Restart After Code Changes

```bash
# Restart all services
sudo systemctl restart marlise.target

# Or restart individual services
sudo systemctl restart marlise-session-manager@pi.service
```

## Service Dependencies

Services start in the correct order automatically:

1. **marlise-mod-host** (base audio engine)
2. **marlise-bridge** (waits for mod-host)
3. **marlise-session-manager** (waits for bridge)
4. **marlise-client-interface** (waits for session manager)
5. **marlise-web-client** (waits for client interface)

If a service fails, dependent services will not start. Use `systemctl status` to diagnose.

## Resource Limits

Each service has built-in resource limits to prevent runaway processes on Raspberry Pi:

- **mod-host**: 256MB RAM, 50% CPU
- **modhost-bridge**: 128MB RAM, 30% CPU
- **session-manager**: 256MB RAM, 40% CPU
- **client-interface**: 256MB RAM, 40% CPU
- **web-client**: 256MB RAM, 30% CPU

**Total:** ~1.1GB RAM max, leaving ~3GB for OS and other processes on Pi 4.

Adjust limits in `.service` files if needed:
```ini
[Service]
MemoryMax=512M
CPUQuota=60%
```

## Security Features

Services include security hardening:

- **NoNewPrivileges**: Prevent privilege escalation
- **PrivateTmp**: Isolated temporary directories
- **ProtectSystem=strict**: Read-only system directories
- **ProtectHome=read-only**: Prevent writing to other users' home
- **ReadWritePaths**: Only `logs/`, `run/`, `data/` are writable

## Troubleshooting

### Services Won't Start

```bash
# Check detailed status
systemctl status marlise-mod-host@pi.service

# View recent logs
journalctl -u marlise-mod-host@pi.service -n 50

# Common issues:
# 1. Binary not found - check ExecStart path in .service file
# 2. Permission denied - ensure user owns marlise directory
# 3. Port already in use - stop conflicting process
```

### Service Keeps Restarting

```bash
# View restart events
journalctl -u marlise-session-manager@pi.service | grep -i restart

# Disable auto-restart temporarily for debugging
sudo systemctl stop marlise-session-manager@pi.service
# Run manually to see errors
cd ~/marlise
.venv/bin/python -m session_manager.main
```

### Check Resource Usage

```bash
# Memory usage
systemctl status marlise-session-manager@pi.service | grep Memory

# All services
systemctl status 'marlise-*@pi.service' | grep -E "Active|Memory|CPU"

# Detailed system resource usage
htop -p $(pgrep -d',' -f marlise)
```

### Audio Not Working

```bash
# Check JACK/PipeWire status
systemctl --user status pipewire
pw-cli info all

# Verify mod-host can access audio
journalctl -u marlise-mod-host@pi.service | grep -i jack

# Test audio manually
pw-jack jack_lsp  # List JACK ports
```

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop marlise.target
sudo systemctl disable marlise.target
sudo systemctl disable 'marlise-*@pi.service'

# Remove service files
sudo rm /etc/systemd/system/marlise*.service
sudo rm /etc/systemd/system/marlise.target

# Reload systemd
sudo systemctl daemon-reload
```

## Next Steps

After installation:

1. **Verify deployment**: Run `../scripts/health-check.sh`
2. **Configure audio**: Set up JACK buffer size, sample rate
3. **Install plugins**: Add LV2 plugins to `/usr/lib/lv2` or `~/.lv2`
4. **Access UI**: Open http://localhost:8888 in browser
5. **Monitor**: Set up log rotation, alerting if needed

## Advanced Configuration

### Custom Environment Variables

Edit service files to add environment variables:

```ini
[Service]
Environment="LOG_LEVEL=DEBUG"
Environment="MODHOST_BRIDGE_TIMEOUT=10.0"
```

### Using Different Ports

```bash
# Edit service files to change ports
sudo nano /etc/systemd/system/marlise-client-interface@.service

# Change CLIENT_INTERFACE_PORT
Environment="CLIENT_INTERFACE_PORT=9090"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart marlise-client-interface@pi.service
```

### Running Multiple Instances

Systemd template units support multiple instances:

```bash
# Install for different users
sudo ./install-systemd.sh user1
sudo ./install-systemd.sh user2

# Start separate instances
sudo systemctl start marlise.target@user1
sudo systemctl start marlise.target@user2
```

## Support

See main repository documentation:
- `../README.md` - Project overview
- `../docs/ARCHITECTURE_OVERVIEW.md` - System architecture
- `../docs/IMPROVEMENT_RECOMMENDATIONS.md` - Performance tuning
- `../QUICK_IMPROVEMENTS.md` - Quick fixes and enhancements
