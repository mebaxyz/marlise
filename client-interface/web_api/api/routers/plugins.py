"""
Plugin/Effect related API endpoints
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Form, File, UploadFile
from fastapi.responses import Response
import json

from ..models import (
    PluginInfo, PluginDetailInfo, PluginAddRequest, PluginBulkRequest,
    PluginConnectionRequest, ParameterSetRequest, ParameterAddressRequest,
    PresetRequest, PresetDeleteRequest, StatusResponse
)

router = APIRouter(prefix="/effect", tags=["plugins"])


@router.get("/list", response_model=List[PluginInfo])
async def get_plugin_list():
    """Get list of all available plugins"""
    # This would call the session manager via ZMQ
    # For now, return empty list as placeholder
    return []


@router.post("/bulk", response_model=Dict[str, PluginDetailInfo])
async def get_plugins_bulk(request: PluginBulkRequest):
    """Get detailed info for multiple plugins at once"""
    # Call session manager with list of URIs
    return {}


@router.get("/get")
async def get_plugin_info(
    uri: str = Query(..., description="Plugin URI"),
    version: Optional[str] = Query(None, description="Plugin version (ignored)"),
    plugin_version: Optional[str] = Query(None, description="Plugin version (ignored)")
):
    """Get detailed information about a specific plugin"""
    # Call session manager for plugin info
    return {}


@router.get("/get_non_cached")
async def get_plugin_info_non_cached(
    uri: str = Query(..., description="Plugin URI")
):
    """Get plugin info bypassing cache (forces fresh scan)"""
    # Call session manager for fresh plugin info
    return {}


@router.get("/add/{instance_id}")
async def add_plugin(
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Plugin URI"),
    x: float = Query(0.0, description="X coordinate"),
    y: float = Query(0.0, description="Y coordinate")
):
    """Add a plugin to the current pedalboard"""
    # Call session manager to add plugin
    return {"ok": False, "message": "Not implemented"}


@router.get("/remove/{instance_id}")
async def remove_plugin(
    instance_id: str = Path(..., description="Plugin instance ID")
):
    """Remove a plugin from the current pedalboard"""
    # Call session manager to remove plugin
    return {"ok": False}


@router.get("/connect/{from_port},{to_port}")
async def connect_ports(
    from_port: str = Path(..., description="Source port"),
    to_port: str = Path(..., description="Destination port")
):
    """Create an audio/MIDI connection between two ports"""
    # Call session manager to connect ports
    return {"ok": False}


@router.get("/disconnect/{from_port},{to_port}")
async def disconnect_ports(
    from_port: str = Path(..., description="Source port"),
    to_port: str = Path(..., description="Destination port")
):
    """Remove an audio/MIDI connection between two ports"""
    # Call session manager to disconnect ports
    return {"ok": False}


@router.post("/parameter/address/{instance_id}/{symbol}")
async def address_parameter(
    instance_id: str = Path(..., description="Plugin instance ID"),
    symbol: str = Path(..., description="Parameter symbol"),
    request: ParameterAddressRequest = None
):
    """Map a plugin parameter to a hardware control or MIDI CC"""
    # Call session manager to create addressing
    return {"ok": False}


@router.post("/parameter/set")
async def set_parameter(data: str = Form(...)):
    """Set plugin parameter value (legacy endpoint with JSON string)"""
    try:
        # Parse the JSON string format: "symbol/instance/portsymbol/value"
        parts = data.strip('"').split('/')
        if len(parts) != 4:
            raise ValueError("Invalid parameter format")
        
        symbol, instance, port_symbol, value = parts
        # Call session manager to set parameter
        return True
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preset/load/{instance_id}")
async def load_preset(
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI")
):
    """Load a preset for a plugin instance"""
    # Call session manager to load preset
    return {"ok": False}


@router.get("/preset/save_new/{instance_id}")
async def save_new_preset(
    instance_id: str = Path(..., description="Plugin instance ID"),
    name: str = Query(..., description="Preset name")
):
    """Create a new preset from current plugin state"""
    # Call session manager to save new preset
    return {"ok": False}


@router.get("/preset/save_replace/{instance_id}")
async def save_replace_preset(
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI"),
    bundle: str = Query(..., description="Bundle path"),
    name: str = Query(..., description="Preset name")
):
    """Overwrite an existing preset with current plugin state"""
    # Call session manager to replace preset
    return {"ok": False}


@router.get("/preset/delete/{instance_id}")
async def delete_preset(
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI"),
    bundle: str = Query(..., description="Bundle path")
):
    """Delete an existing user preset"""
    # Call session manager to delete preset
    return {"ok": False}


@router.get("/image/{image_type}.png")
async def get_plugin_image(
    image_type: str = Path(..., description="Image type: screenshot or thumbnail"),
    uri: str = Query(..., description="Plugin URI"),
    v: Optional[str] = Query(None, description="Version parameter")
):
    """Get plugin GUI screenshot or thumbnail image"""
    # Return plugin image from filesystem or default
    return Response(content=b"", media_type="image/png")


@router.get("/file/{file_type}")
async def get_plugin_file(
    file_type: str = Path(..., description="File type: iconTemplate, settingsTemplate, stylesheet, javascript"),
    uri: str = Query(..., description="Plugin URI")
):
    """Get plugin GUI template files and resources"""
    # Return plugin file content
    return Response(content="", media_type="text/plain")


@router.get("/file/custom")
async def get_plugin_custom_file(
    filename: str = Query(..., description="Relative filename"),
    uri: str = Query(..., description="Plugin URI")
):
    """Get custom plugin GUI assets (images, WASM, etc.)"""
    # Return custom plugin file
    return Response(content=b"", media_type="application/octet-stream")


@router.post("/install")
async def install_plugin(file: UploadFile = File(...)):
    """Install a plugin package from uploaded bundle file"""
    # Process uploaded plugin bundle
    return {
        "ok": False,
        "installed": [],
        "removed": [],
        "error": "Not implemented"
    }