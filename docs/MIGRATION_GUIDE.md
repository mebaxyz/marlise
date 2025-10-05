# Migration Guide: From Submodules to Integrated Structure

This document explains the changes made to the repository structure and how to adapt to the new organization.

## What Changed?

The repository has been reorganized from a submodule-based structure to an integrated, self-explanatory folder structure.

### Before (Old Structure with Submodules)

```
marlise/
├── .gitmodules                           # Submodule configuration
├── mado-audio-host/                      # Git submodule
│   ├── mod-host/                         # Audio engine binary
│   ├── modhost-bridge/                   # Bridge binary
│   └── session-manager/                  # Session manager
├── mod-ui/                               # Git submodule (web interface)
├── scripts/                              # Scripts
├── COMMUNICATION_ARCHITECTURE.md         # Root-level docs
├── COMMUNICATION_FLOW_DIAGRAMS.md
├── COMMUNICATION_QUICK_REFERENCE.md
├── test_api_completeness.py             # Root-level tests
├── test_http_api.py
└── test_zmq_communication.py
```

### After (New Integrated Structure)

```
marlise/
├── audio-engine/                         # Low-level audio processing
│   ├── mod-host/                         # LV2 plugin host (C)
│   └── modhost-bridge/                   # JSON-RPC bridge (C++)
├── session-manager/                      # High-level orchestration (Python)
│   └── src/                              # Session manager source
├── client-interface/                     # Web API and UI (FastAPI)
│   ├── api/                              # FastAPI backend
│   └── web/                              # Web client
├── scripts/                              # Start/stop scripts
├── docs/                                 # All documentation
│   ├── ARCHITECTURE_OVERVIEW.md          # New comprehensive overview
│   ├── COMMUNICATION_ARCHITECTURE.md
│   ├── COMMUNICATION_FLOW_DIAGRAMS.md
│   └── COMMUNICATION_QUICK_REFERENCE.md
├── tests/                                # Integration tests
│   ├── test_api_completeness.py
│   ├── test_http_api.py
│   └── test_zmq_communication.py
├── .gitignore                            # New comprehensive gitignore
├── STRUCTURE.md                          # New quick reference guide
└── README.md                             # Updated with new structure
```

## Key Improvements

### 1. **Self-Explanatory Names**
- `audio-engine/` clearly indicates low-level audio processing
- `session-manager/` indicates high-level orchestration
- `client-interface/` indicates user-facing components

### 2. **No More Submodules**
- All code is directly in the repository
- No need for `git submodule update --init --recursive`
- Easier to clone and work with
- Single version control history

### 3. **Organized Documentation**
- All documentation in `docs/` folder
- Added comprehensive `ARCHITECTURE_OVERVIEW.md`
- Added `STRUCTURE.md` for quick navigation

### 4. **Organized Tests**
- All tests in `tests/` folder
- Consistent location for integration tests

### 5. **Better Gitignore**
- Comprehensive `.gitignore` added
- Build artifacts properly excluded
- Runtime files (logs, PIDs) excluded

## How to Migrate

### For Existing Clones

If you have an existing clone with initialized submodules:

```bash
# 1. Backup any local changes
git stash

# 2. Pull the new structure
git fetch origin
git checkout <new-branch-name>

# 3. Clean up old submodules
rm -rf mado-audio-host mod-ui
git submodule deinit --all -f

# 4. Verify new structure
ls -la
# You should see: audio-engine/, session-manager/, client-interface/, docs/, tests/
```

### For New Clones

Simply clone normally - no special commands needed:

```bash
git clone https://github.com/mebaxyz/marlise.git
cd marlise
```

## Path Updates Required

### Scripts

The start scripts have been automatically updated:

**Old paths**:
```bash
$ROOT_DIR/mado-audio-host/mod-host/mod-host
$ROOT_DIR/mado-audio-host/modhost-bridge/build/modhost-bridge
$ROOT_DIR/mado-audio-host/session-manager/start_session_manager.sh
```

**New paths**:
```bash
$ROOT_DIR/audio-engine/mod-host/mod-host
$ROOT_DIR/audio-engine/modhost-bridge/build/modhost-bridge
$ROOT_DIR/session-manager/start_session_manager.sh
```

### Environment Variables

If you have custom environment variables set, update them:

**Old**:
```bash
export MOD_HOST_BIN=/path/to/marlise/mado-audio-host/mod-host/mod-host
export SESSION_MANAGER_SCRIPT=/path/to/marlise/mado-audio-host/session-manager/start_session_manager.sh
```

**New**:
```bash
export MOD_HOST_BIN=/path/to/marlise/audio-engine/mod-host/mod-host
export SESSION_MANAGER_SCRIPT=/path/to/marlise/session-manager/start_session_manager.sh
```

### Import Paths (if applicable)

If you have Python scripts that import from the session manager or client interface:

**Old**:
```python
# Not applicable - code was in submodules
```

**New**:
```python
from session_manager.src import session_manager
from client_interface.api import main
```

## Documentation Updates

### Updated Files
- `README.md` - Reflects new structure, removed submodule instructions
- `scripts/README.md` - Updated paths
- `scripts/start-service.sh` - Updated binary paths

### New Files
- `docs/ARCHITECTURE_OVERVIEW.md` - Comprehensive system overview
- `STRUCTURE.md` - Quick navigation guide
- `.gitignore` - Comprehensive ignore rules
- Component README files in each major folder

## Testing the Migration

After migrating, verify everything works:

```bash
# 1. Check structure
ls -la
# Should show: audio-engine/, session-manager/, client-interface/, docs/, tests/

# 2. Verify scripts can find binaries (will fail if binaries not built, but paths should be correct)
./scripts/start-service.sh
# Should report correct paths, even if binaries don't exist yet

# 3. Run tests (if services are running)
python tests/test_zmq_communication.py
python tests/test_http_api.py
```

## Benefits of New Structure

### For Developers
- ✅ Easier to find code - folder names match architecture layers
- ✅ Clear separation of concerns
- ✅ Better IDE navigation
- ✅ Simpler git operations (no submodules)
- ✅ Comprehensive documentation in one place

### For New Contributors
- ✅ Self-explanatory structure - can understand layout immediately
- ✅ Easy to clone - no submodule complexity
- ✅ Clear component boundaries
- ✅ Better README with component links

### For Maintenance
- ✅ Single version history
- ✅ Atomic commits across all components
- ✅ Easier dependency management
- ✅ Simpler CI/CD setup
- ✅ Better `.gitignore` prevents accidental commits

## Troubleshooting

### Issue: Can't find binaries after migration

**Solution**: The binaries need to be built. See each component's README:
- `audio-engine/README.md` for mod-host and modhost-bridge
- `session-manager/README.md` for session manager
- `client-interface/README.md` for client interface

### Issue: Scripts fail with "file not found"

**Solution**: Make sure you've pulled the latest changes and the paths in `scripts/start-service.sh` use the new structure. If you have custom environment variables, update them as shown above.

### Issue: Old submodule directories still exist

**Solution**: 
```bash
rm -rf mado-audio-host mod-ui
git submodule deinit --all -f
```

## Questions?

If you have questions about the migration or new structure:
1. Check `STRUCTURE.md` for quick reference
2. Read `docs/ARCHITECTURE_OVERVIEW.md` for detailed explanation
3. Look at component README files for specific details
4. Refer to `docs/COMMUNICATION_ARCHITECTURE.md` for protocol details
