import os
import sys
import json
import shutil
import asyncio
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from os.path import join

DATA_DIR = os.environ.get('MOD_DATA_DIR', os.path.expanduser('~/data'))
# Assume these constants are defined elsewhere
MODEL_CPU = os.environ.get('MOD_MODEL_CPU', None)
MODEL_TYPE = os.environ.get('MOD_MODEL_TYPE', None)
USER_BANKS_JSON_FILE = os.environ.get('MOD_USER_BANKS_JSON', join(DATA_DIR, 'banks.json'))
FAVORITES_JSON_FILE = os.environ.get('MOD_FAVORITES_JSON', join(DATA_DIR, 'favorites.json'))
KEYS_PATH = os.environ.get('MOD_KEYS_PATH', join(DATA_DIR, 'keys'))

# It's mandatory KEYS_PATH ends with / and is in MOD_KEYS_PATH,
# so utils_lilv.so can properly access it
if not KEYS_PATH.endswith('/'):
    KEYS_PATH += '/'
os.environ['MOD_KEYS_PATH'] = KEYS_PATH

LV2_PLUGIN_DIR = os.environ.get('MOD_USER_PLUGINS_DIR', os.path.expanduser("~/.lv2"))
LV2_PEDALBOARDS_DIR = os.environ.get('MOD_USER_PEDALBOARDS_DIR', os.path.expanduser("~/.pedalboards"))
UPDATE_MOD_OS_FILE='/data/{}'.format(os.environ.get('MOD_UPDATE_MOD_OS_FILE', 'modduo.tar').replace('*','cloud'))
UPDATE_MOD_OS_HERLPER_FILE='/data/boot-restore'


# Mocked or assumed external functions and constants
def get_hardware_descriptor():
    """Mocks the function to get hardware information."""
    return {
        "name": "MOD Duo X",
        "architecture": "aarch64",
        "cpu": "Quad-core ARM",
        "platform": "Linux",
        "bin-compat": "mod-host",
        "model": "MODX"
    }

def run_command(cmd, timeout=None):
    """Mocks running a shell command asynchronously."""
    # In a real application, you'd use a library like `subprocess` or `asyncio.create_subprocess_exec`
    # to run external commands. For this example, we'll just mock the result.
    print(f"Executing command: {cmd}")
    # Example mock return: (exit_code, stdout_bytes, stderr_bytes)
    if cmd[0] == "reboot":
        return (0, b"", b"")
    elif cmd[0] == "rm":
        # Simulate successful removal
        return (0, b"", b"")
    elif cmd[0] == "systemctl":
        # Simulate successful service start/stop
        return (0, b"", b"")
    elif cmd[0] == "mod-backup":
        # Simulate successful backup
        return (0, b"Backup successful.", b"")
    return (0, b"", b"")

async def restart_services(restart_jack: bool, do_sync: bool):
    """Mocks restarting services."""
    print(f"Restarting services (restart_jack: {restart_jack}, do_sync: {do_sync})")
    await asyncio.sleep(1)
    print("Services restarted.")



# Pydantic models for request bodies
class CleanupRequest(BaseModel):
    banks: bool = False
    favorites: bool = False
    hmiSettings: bool = False
    licenseKeys: bool = False
    pedalboards: bool = False
    plugins: bool = False

class ExeChangeFileCreateRequest(BaseModel):
    path: str
    create: bool

class ExeChangeFileWriteRequest(BaseModel):
    path: str
    content: str

class ExeChangeServiceRequest(BaseModel):
    name: str
    enable: bool
    inverted: bool
    persistent: bool

# Root FastAPI instance and router
app = FastAPI(
    title="System API",
    description="A rewrite of the system endpoints using FastAPI.",
    version="1.0.0"
)
router = APIRouter(prefix="/system")

# --- Endpoints ---

@router.get("/info", tags=["System Info"])
async def get_system_info():
    """
    Retrieves information about the system's hardware,
    firmware, and Python environment.
    """
    hwdesc = get_hardware_descriptor()
    uname = os.uname()

    sysdate = "Unknown"
    if os.path.exists("/etc/mod-release/system"):
        with open("/etc/mod-release/system") as fh:
            line = fh.readline().strip()
            if "generated=" in line:
                sysdate = line.split("generated=", 1)[1].split(" at ", 1)[0].strip()

    info = {
        "hwname": hwdesc.get('name', "Unknown"),
        "architecture": hwdesc.get('architecture', "Unknown"),
        "cpu": MODEL_CPU or hwdesc.get('cpu', "Unknown"),
        "platform": hwdesc.get('platform', "Unknown"),
        "bin_compat": hwdesc.get('bin-compat', "Unknown"),
        "model": MODEL_TYPE or hwdesc.get('model', "Unknown"),
        "sysdate": sysdate,
        "python": {
            "version": sys.version
        },
        "uname": {
            "machine": uname.machine,
            "release": uname.release,
            "sysname": uname.sysname,
            "version": uname.version
        }
    }
    return info

@router.post("/cleanup", tags=["System Maintenance"])
async def system_cleanup(cleanup_data: CleanupRequest):
    """
    Cleans up specified system data like banks, favorites, and plugins.
    """
    stuff_to_delete = []

    if cleanup_data.banks:
        stuff_to_delete.append(USER_BANKS_JSON_FILE)
    if cleanup_data.favorites:
        stuff_to_delete.append(FAVORITES_JSON_FILE)
    if cleanup_data.licenseKeys:
        stuff_to_delete.append(KEYS_PATH)
    if cleanup_data.pedalboards:
        stuff_to_delete.append(LV2_PEDALBOARDS_DIR)
    if cleanup_data.plugins:
        stuff_to_delete.append(LV2_PLUGIN_DIR)
        
    # Check for hmiSettings and hmi_eeprom
    if cleanup_data.hmiSettings and get_hardware_descriptor().get('hmi_eeprom', False):
        print("Resetting HMI EEPROM and running hmi-reset")
        # Assuming SESSION.hmi and run_command are async-compatible
        await run_command(["hmi-reset"])

    if not stuff_to_delete and not cleanup_data.hmiSettings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nothing to delete."
        )

    if cleanup_data.plugins:
        # Assuming `run_command` can run systemctl
        await run_command(["systemctl", "stop", "jack2"])

    if stuff_to_delete:
        await run_command(["rm", "-rf"] + stuff_to_delete)

    restart_jack2 = cleanup_data.pedalboards or cleanup_data.plugins
    asyncio.create_task(restart_services(restart_jack2, True))

    return {"ok": True, "error": ""}

@router.get("/prefs", tags=["System Configuration"])
async def get_system_preferences():
    """
    Retrieves system preferences based on the existence or content of specific files.
    """
    prefs_list = [
        {"label": "bluetooth_name", "type": "contents", "data": "/data/bluetooth/name", "valtype": str, "valdef": "Unknown"},
        {"label": "jack_mono_copy", "type": "exists", "data": "/data/jack-mono-copy"},
        {"label": "jack_sync_mode", "type": "exists", "data": "/data/jack-sync-mode"},
        {"label": "jack_256_frames", "type": "exists", "data": "/data/using-256-frames"},
        {"label": "separate_spdif_outs", "type": "exists", "data": "/data/separate-spdif-outs"},
        {"label": "service_mod_peakmeter", "type": "not_exists", "data": "/data/disable-mod-peakmeter"},
        {"label": "service_mod_sdk", "type": "exists", "data": "/data/enable-mod-sdk"},
        {"label": "service_netmanager", "type": "exists", "data": "/data/enable-netmanager"},
        {"label": "autorestart_hmi", "type": "exists", "data": "/data/autorestart-hmi"}
    ]
    
    ret = {}
    for pref in prefs_list:
        label, pref_type, data = pref["label"], pref["type"], pref["data"]
        val = None

        if pref_type == "exists":
            val = os.path.exists(data)
        elif pref_type == "not_exists":
            val = not os.path.exists(data)
        elif pref_type == "contents":
            if os.path.exists(data):
                with open(data, 'r') as fh:
                    content = fh.read().strip()
                try:
                    val = pref.get('valtype', str)(content)
                except:
                    val = pref.get('valdef', None)
            else:
                val = pref.get('valdef', None)
        
        ret[label] = val
    
    return ret

@router.post("/exechange", tags=["System Maintenance"])
async def system_exechange(request: Request, etype: str = Form(...), payload: Optional[str] = Form(None)):
    """
    Handles various system execution changes like reboot, backup, and service management.
    """
    if etype == "command":
        cmd_parts = payload.split(" ", 1)
        cmd = cmd_parts[0]
        cdata = cmd_parts[1] if len(cmd_parts) > 1 else ""

        if cmd == "reboot":
            await run_command(["hmi-reset"])
            asyncio.create_task(run_command(["reboot"]))
            return {"ok": True}
        elif cmd == "restore":
            asyncio.create_task(run_command(["restore"]))
            return {"ok": True}
        elif cmd == "backup-export":
            args = ["mod-backup", "backup"]
            if cdata.split(",")[0] == "1":
                args.append("-d")
            if cdata.split(",")[1] == "1":
                args.append("-p")
            resp = await run_command(args)
            error = resp[2].decode("utf-8", errors="ignore").strip()
            if len(error) > 1:
                error = error[0].upper() + error[1:] + "."
            return {"ok": resp[0] == 0, "error": error}
        elif cmd == "backup-import":
            args = ["mod-backup", "restore"]
            if cdata.split(",")[0] == "1":
                args.append("-d")
            if cdata.split(",")[1] == "1":
                args.append("-p")
            resp = await run_command(args)
            error = resp[2].decode("utf-8", errors="ignore").strip()
            if len(error) > 1:
                error = error[0].upper() + error[1:] + "."
            
            if resp[0] == 0:
                asyncio.create_task(restart_services(True, False))
            return {"ok": resp[0] == 0, "error": error}
        else:
            return {"ok": False}
    
    elif etype == "filecreate":
        data = ExeChangeFileCreateRequest(path=payload, create=bool(int(request.query_params.get('create'))))
        
        allowed_paths = ["autorestart-hmi", "jack-mono-copy", "jack-sync-mode", "separate-spdif-outs", "using-256-frames"]
        if data.path not in allowed_paths:
            return {"ok": False}
        
        filename = "/data/" + data.path
        if data.create:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as fh:
                fh.write("")
        elif os.path.exists(filename):
            os.remove(filename)
        return {"ok": True}

    elif etype == "filewrite":
        data = ExeChangeFileWriteRequest(path=payload, content=request.query_params.get('content', "").strip())
        
        allowed_paths = ["bluetooth/name"]
        if data.path not in allowed_paths:
            return {"ok": False}

        filename = "/data/" + data.path
        if data.content:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as fh:
                fh.write(data.content)
        elif os.path.exists(filename):
            os.remove(filename)
        return {"ok": True}

    elif etype == "service":
        data = ExeChangeServiceRequest(
            name=payload, 
            enable=bool(int(request.query_params.get('enable'))),
            inverted=bool(int(request.query_params.get('inverted'))),
            persistent=bool(int(request.query_params.get('persistent')))
        )
        
        allowed_names = ["hmi-update", "mod-peakmeter", "mod-sdk", "netmanager"]
        if data.name not in allowed_names:
            return {"ok": False}
        
        if data.inverted:
            data.enable = not data.enable

        servicename = data.name if data.name != "netmanager" else "jack-netmanager"
        
        if data.persistent:
            checkname = f"/data/{'disable' if data.inverted else 'enable'}-{data.name}"
            if data.enable:
                os.makedirs(os.path.dirname(checkname), exist_ok=True)
                with open(checkname, 'w') as fh:
                    fh.write("")
            elif os.path.exists(checkname):
                os.remove(checkname)
        
        if data.name == "hmi-update":
            return {"ok": True}
        
        await run_command(["systemctl", "start" if data.enable else "stop", servicename])
        return {"ok": True}

    return {"ok": False}

@router.post("/update/download", tags=["System Update"])
async def upload_update_file(file: UploadFile = File(...)):
    """
    Receives an OS update file and saves it to a temporary location.
    """
    destination_dir = "/tmp/os-update"
    os.makedirs(destination_dir, exist_ok=True)
    
    file_path = os.path.join(destination_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Move the file to the final destination
        await run_command(["mv", file_path, UPDATE_MOD_OS_FILE])
        
        return {"ok": True, "filename": file.filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {e}"
        )

@router.post("/update/begin", tags=["System Update"])
async def begin_update():
    """
    Starts the OS update process if the update file exists.
    """
    if not os.path.exists(UPDATE_MOD_OS_FILE):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update file not found."
        )
    
    with open(UPDATE_MOD_OS_HERLPER_FILE, 'w') as fh:
        fh.write("")
        
    asyncio.create_task(run_command(["start-restore"]))
    return {"ok": True}

@router.post("/package/uninstall", tags=["Package Management"])
async def uninstall_packages(bundles: List[str]):
    """
    Uninstalls a list of specified packages (plugins).
    """
    error = ""
    removed = []

    for bundlepath in bundles:
        if os.path.exists(bundlepath) and os.path.isdir(bundlepath):
            if not os.path.abspath(bundlepath).startswith(LV2_PLUGIN_DIR):
                error = f"bundlepath '{bundlepath}' is not in LV2_PATH"
                break
            
            # The original code had a call to SESSION.host.remove_bundle,
            # which is an external dependency. We'll mock its behavior.
            # Assuming it returns (success_status, data)
            resp = (True, [bundlepath.split("/")[-1]]) 

            if resp[0]:
                removed += resp[1]
                shutil.rmtree(bundlepath)
            else:
                error = resp[1]
                break
        else:
            print(f"bundlepath is non-existent: {bundlepath}")

    if error:
        return {"ok": False, "error": error, "removed": removed}
    
    if len(removed) == 0:
        return {"ok": False, "error": "No plugins found", "removed": []}
    
    # Original logic for re-saving banks and resetting cache
    if len(removed) > 0:
        print("Re-saving banks and resetting cache...")

    return {"ok": True, "removed": removed}

# Include the router in the main app
app.include_router(router)