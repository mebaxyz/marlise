# Quick Improvement Checklist

This is a condensed, actionable version of `docs/IMPROVEMENT_RECOMMENDATIONS.md`. Pick any item and start!

## ⚡ Quick Wins (< 1 hour each)

### 1. Add uvloop for 2-4x I/O performance
```bash
# Add to client-interface/web_api/api/requirements.txt
echo "uvloop>=0.17.0" >> client-interface/web_api/api/requirements.txt

# Add to client-interface/web_api/api/main.py (top of file, before other imports)
# import uvloop
# uvloop.install()
```

### 2. Create development helper scripts
```bash
# Already have these in scripts/, could add:
# - scripts/dev-health-check.sh (curl all health endpoints)
# - scripts/dev-logs-tail.sh (tail -f logs/*.log)
# - scripts/dev-restart-quick.sh (restart only changed service)
```

### 3. Fix Docker networking for dev
```bash
# In docker-compose.dev.yml, change CLIENT_INTERFACE_ZMQ_HOST to 127.0.0.1
# and use network_mode: host for development simplicity
```

### 4. Add basic metrics endpoint
```python
# In session_manager/managers/session_manager.py
# Add method to return uptime, memory, request counts
```

---

## 🔥 Critical (Do This Week)

### Priority 1: Auto-Reconnect for Bridge Client
**File:** `session_manager/infrastructure/bridge_client.py`  
**Add:** Background task that detects disconnection and reconnects automatically  
**Benefit:** Service survives bridge crashes without manual restart

### Priority 2: Request Timeouts
**Files:** All routers in `client-interface/web_api/api/routers/*.py`  
**Change:** Add `timeout=5.0` to all `zmq_client.call()` invocations  
**Benefit:** UI doesn't freeze if backend stalls

### Priority 3: Systemd Service Units
**Create:** `deployment/systemd/*.service` files  
**Benefit:** Production-grade service management with auto-restart

---

## 🧹 Code Cleanup (Background Task)

### Fix Lint Issues
```bash
# Run ruff auto-fix
ruff check --fix .

# Then manually review:
ruff check .
```

**Focus files:**
- `config-service/main.py` (18 issues)
- `client-interface/web_api/api/routers/plugins.py` (23 issues)
- `client-interface/web_api/api/main.py` (5 issues)

### Address TODOs
Search for `# TODO` and either:
1. Implement the feature
2. Create a GitHub issue
3. Remove if not needed

**High-priority TODOs:**
- `routers/auth.py` - Token persistence
- `routers/snapshots.py` - Snapshot save/load
- `routers/jack.py` - MIDI configuration

---

## 📊 Monitoring & Observability

### Add Health Check Endpoint
```python
# In client-interface/web_api/api/routers/system.py
@router.get("/health/deep")
async def deep_health_check(request: Request):
    # Test: client -> session_manager -> bridge -> mod-host
    # Return: service status for each layer
```

### WebSocket Event Broadcasting
```python
# In session_manager - publish events
# In client_interface - subscribe and forward to WebSocket clients
# Events: plugin.loaded, parameter.changed, connection.created
```

---

## 🚀 Performance Optimization

### Response Caching
**File:** `session_manager/managers/plugin_manager.py`  
**Add:** LRU cache with 30s TTL for plugin list, metadata  
**Benefit:** 30-50% reduction in ZMQ round-trips

### Merge Config Service
**Action:** Move config-service into session_manager as a module  
**Benefit:** Reduce memory footprint by ~50MB, fewer processes

### Optimize Logging
**Change:** Log to stdout (INFO), rotate files (WARNING+), limit size  
**Benefit:** Less SD card wear, better Pi performance

---

## 📝 Documentation Needed

### Create These Docs:
1. **`docs/RASPBERRY_PI_DEPLOYMENT.md`**
   - Hardware requirements
   - OS setup
   - Service installation
   - Performance tuning

2. **`docs/TROUBLESHOOTING.md`**
   - Common errors and fixes
   - Health check procedures
   - Log analysis guide

3. **`docs/API_REFERENCE.md`**
   - All HTTP endpoints
   - ZMQ RPC methods
   - WebSocket events

---

## 🧪 Testing Improvements

### Add Unit Tests for Core Logic
```bash
# Create tests for:
session_manager/tests/test_plugin_manager_unit.py
session_manager/tests/test_session_manager_unit.py
session_manager/tests/test_connection_manager_unit.py
```

### Mock ZMQ in Tests
```python
# Use pytest-mock to avoid requiring real services
# Test business logic in isolation
```

---

## 🎯 Immediate Action Plan

**Today (2 hours):**
1. Add uvloop (15 min)
2. Add request timeouts (30 min)
3. Create dev helper scripts (45 min)
4. Run ruff auto-fix (15 min)
5. Test everything (15 min)

**This Week (1 day):**
1. Implement auto-reconnect (3 hours)
2. Create systemd units (3 hours)
3. Add deep health check (2 hours)

**This Month:**
1. Response caching (3 hours)
2. Fix all lint issues (8 hours)
3. Complete high-priority TODOs (12 hours)
4. Write Pi deployment guide (4 hours)
5. Add metrics endpoint (4 hours)

---

## 📈 Success Metrics

After improvements, you should see:

**Performance:**
- ⚡ 2-4x faster I/O (uvloop)
- 💾 30-50% less ZMQ traffic (caching)
- 🧠 10-15% less memory (merge services)

**Reliability:**
- ⏰ 99.9%+ uptime (auto-reconnect + systemd)
- 🛡️ No UI freezes (timeouts)
- 🔄 Auto-recovery from crashes

**Code Quality:**
- ✅ 0 lint errors, < 10 warnings
- 📝 All TODOs resolved or tracked
- 🧪 70%+ test coverage

---

## 🆘 Need Help?

Refer to full analysis: `docs/IMPROVEMENT_RECOMMENDATIONS.md`

**Quick checks:**
```bash
# Check service health
curl http://localhost:8080/health
curl http://localhost:8888/

# Check logs
tail -f logs/*.log

# Check processes
ps aux | grep -E "python|mod-host|modhost-bridge"

# Check ports
netstat -tuln | grep -E "8080|8888|5555|6000|5718"
```
