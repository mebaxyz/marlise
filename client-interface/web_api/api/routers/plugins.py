"""
Plugin/Effect related API endpoints
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Form, File, UploadFile, Body, Request
from fastapi.responses import Response
import json

from ..models import (
    PluginInfo, PluginDetailInfo, PluginAddRequest, PluginBulkRequest,
    PluginConnectionRequest, ParameterSetRequest, ParameterAddressRequest,
    PresetRequest, PresetDeleteRequest, StatusResponse
)

import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/effect", tags=["plugins"])


@router.get("/list", response_model=List[PluginInfo])
async def get_plugin_list(request: Request):
    """Get list of all available plugins."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        logger.debug("zmq_client not available, returning empty plugin list")
        return []

    try:
        fut = zmq_client.call("session_manager", "list_plugins")
        resp = await asyncio.wait_for(fut, timeout=3.0)

        # Expecting resp to be an iterable of dict-like plugin info objects
        plugins = []
        if isinstance(resp, list):
            items = resp
        elif isinstance(resp, dict):
            # some services may return {"plugins": [...]}
            items = resp.get("plugins") or resp.get("result") or []
        else:
            items = []

        for p in items:
            try:
                plugins.append(PluginInfo(
                    uri=p.get("uri") if isinstance(p, dict) else p["uri"],
                    name=p.get("name") if isinstance(p, dict) else p["name"],
                    category=p.get("category") if isinstance(p, dict) else p.get("category", []),
                    version=str(p.get("version", "")) if isinstance(p, dict) else str(p.get("version", "")),
                    microVersion=int(p.get("microVersion", 0)),
                    minorVersion=int(p.get("minorVersion", 0)),
                    release=int(p.get("release", 0)),
                    builder=p.get("builder", "")
                ))
            except Exception:
                logger.debug("Skipping invalid plugin entry: %r", p)

        return plugins
    except asyncio.TimeoutError:
        logger.warning("list_plugins timed out")
        return []
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error calling list_plugins: %s", exc)
        return []


@router.post("/bulk", response_model=Dict[str, PluginDetailInfo])
async def get_plugins_bulk(request_http: Request, request: PluginBulkRequest):
    """Get detailed info for multiple plugins at once."""
    zmq_client = getattr(request_http.app.state, "zmq_client", None)
    if zmq_client is None:
        return {}

    try:
        fut = zmq_client.call("session_manager", "get_plugins_bulk", uris=request.uris)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return resp.get("plugins", {}) if isinstance(resp, dict) else {}
    except asyncio.TimeoutError:
        logger.warning("get_plugins_bulk timed out")
        return {}
    except Exception as exc:
        logger.exception("Error calling get_plugins_bulk: %s", exc)
        return {}


@router.get("/get")
async def get_plugin_info(
    request: Request,
    uri: str = Query(..., description="Plugin URI"),
    version: Optional[str] = Query(None, description="Plugin version (ignored)"),
    plugin_version: Optional[str] = Query(None, description="Plugin version (ignored)")
):
    """Get detailed information about a specific plugin."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {}

    try:
        fut = zmq_client.call("session_manager", "get_plugin_info_by_uri", uri=uri)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return resp.get("plugin", {}) if isinstance(resp, dict) and resp.get("success") else {}
    except asyncio.TimeoutError:
        logger.warning("get_plugin_info_by_uri timed out")
        return {}
    except Exception as exc:
        logger.exception("Error calling get_plugin_info_by_uri: %s", exc)
        return {}


@router.get("/get_non_cached")
async def get_plugin_info_non_cached(
    uri: str = Query(..., description="Plugin URI")
):
    """NOT IMPLEMENTED: Get plugin info bypassing cache (forces fresh scan).

    TODO: call session manager forcing a fresh LV2 scan.
    """
    # Call session manager for fresh plugin info
    return {}


@router.get("/add/{instance_id}")
async def add_plugin(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Plugin URI"),
    x: float = Query(0.0, description="X coordinate"),
    y: float = Query(0.0, description="Y coordinate")
):
    """Add a plugin to the current pedalboard."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False, "message": "ZMQ client not available"}

    try:
        fut = zmq_client.call("session_manager", "add_plugin", uri=uri, x=x, y=y)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return resp.get("plugin", {})
        else:
            return {"ok": False, "message": resp.get("error", "Unknown error")}
    except asyncio.TimeoutError:
        logger.warning("add_plugin timed out")
        return {"ok": False, "message": "Request timed out"}
    except Exception as exc:
        logger.exception("Error calling add_plugin: %s", exc)
        return {"ok": False, "message": str(exc)}


@router.get("/remove/{instance_id}")
async def remove_plugin(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID")
):
    """Remove a plugin from the current pedalboard."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "remove_plugin", instance_id=instance_id)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("remove_plugin timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling remove_plugin: %s", exc)
        return {"ok": False}


@router.get("/connect/{from_port},{to_port}")
async def connect_ports(
    request: Request,
    from_port: str = Path(..., description="Source port"),
    to_port: str = Path(..., description="Destination port")
):
    """Create an audio/MIDI connection between two ports."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "connect_jack_ports", port1=from_port, port2=to_port)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("connect_jack_ports timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling connect_jack_ports: %s", exc)
        return {"ok": False}


@router.get("/disconnect/{from_port},{to_port}")
async def disconnect_ports(
    request: Request,
    from_port: str = Path(..., description="Source port"),
    to_port: str = Path(..., description="Destination port")
):
    """Remove an audio/MIDI connection between two ports."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "disconnect_jack_ports", port1=from_port, port2=to_port)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("disconnect_jack_ports timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling disconnect_jack_ports: %s", exc)
        return {"ok": False}


@router.post("/parameter/address/{instance_id}/{symbol}")
async def address_parameter(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID"),
    symbol: str = Path(..., description="Parameter symbol"),
    body: ParameterAddressRequest = Body(...)
):
    """Map a plugin parameter to a hardware control or MIDI CC."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        # Merge path parameters with request body
        params = {
            "instance_id": instance_id,
            "symbol": symbol,
            **body.dict()
        }
        fut = zmq_client.call("session_manager", "address_parameter", **params)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("address_parameter timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling address_parameter: %s", exc)
        return {"ok": False}


@router.post("/parameter/set")
async def set_parameter(request: Request, data: str = Form(...)):
    """Set plugin parameter value (legacy endpoint with JSON string)."""
    try:
        # Parse the JSON string format: "symbol/instance/portsymbol/value"
        parts = data.strip('"').split('/')
        if len(parts) != 4:
            raise ValueError("Invalid parameter format")
        
        symbol, instance, port_symbol, value_str = parts
        value = float(value_str)
        
        zmq_client = getattr(request.app.state, "zmq_client", None)
        if zmq_client is None:
            return False

        fut = zmq_client.call("session_manager", "set_parameter", instance_id=instance, parameter=port_symbol, value=value)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return isinstance(resp, dict) and resp.get("success", False)
    except asyncio.TimeoutError:
        logger.warning("set_parameter timed out")
        return False
    except Exception as e:
        logger.exception("Error calling set_parameter: %s", e)
        return False


@router.get("/preset/load/{instance_id}")
async def load_preset(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI")
):
    """Load a preset for a plugin instance."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "load_preset", instance_id=instance_id, uri=uri, label=uri)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("load_preset timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling load_preset: %s", exc)
        return {"ok": False}


@router.get("/preset/save_new/{instance_id}")
async def save_new_preset(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID"),
    name: str = Query(..., description="Preset name")
):
    """Create a new preset from current plugin state."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        uri = f"preset://{instance_id}/{name}"
        fut = zmq_client.call("session_manager", "save_preset", instance_id=instance_id, uri=uri, label=name, directory="")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("save_preset timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling save_preset: %s", exc)
        return {"ok": False}


@router.get("/preset/save_replace/{instance_id}")
async def save_replace_preset(
    request: Request,
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI"),
    bundle: str = Query(..., description="Bundle path"),
    name: str = Query(..., description="Preset name")
):
    """Overwrite an existing preset with current plugin state."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "save_preset", instance_id=instance_id, uri=uri, label=name, directory=bundle)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("save_preset timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling save_preset: %s", exc)
        return {"ok": False}


@router.get("/preset/delete/{instance_id}")
async def delete_preset(
    instance_id: str = Path(..., description="Plugin instance ID"),
    uri: str = Query(..., description="Preset URI"),
    bundle: str = Query(..., description="Bundle path")
):
    """NOT IMPLEMENTED: Delete an existing user preset.

    TODO: remove preset file via session manager and return success boolean.
    """
    # Call session manager to delete preset
    return {"ok": False}


@router.get("/image/{image_type}.png")
async def get_plugin_image(
    request: Request,
    image_type: str = Path(..., description="Image type: screenshot or thumbnail"),
    uri: str = Query(..., description="Plugin URI"),
    v: Optional[str] = Query(None, description="Version parameter")
):
    """Get plugin GUI screenshot or thumbnail image."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return Response(content=b"", media_type="image/png")

    try:
        fut = zmq_client.call("session_manager", "get_plugin_image", plugin_uri=uri, image_type=image_type)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            # Assume the response contains base64 encoded image data
            # For now, return empty image
            return Response(content=b"", media_type="image/png")
        else:
            return Response(content=b"", media_type="image/png")
    except asyncio.TimeoutError:
        logger.warning("get_plugin_image timed out")
        return Response(content=b"", media_type="image/png")
    except Exception as exc:
        logger.exception("Error calling get_plugin_image: %s", exc)
        return Response(content=b"", media_type="image/png")


@router.get("/file/{file_type}")
async def get_plugin_file(
    request: Request,
    file_type: str = Path(..., description="File type: iconTemplate, settingsTemplate, stylesheet, javascript"),
    uri: str = Query(..., description="Plugin URI")
):
    """Get plugin GUI template files and resources."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return Response(content="", media_type="text/plain")

    try:
        fut = zmq_client.call("session_manager", "get_plugin_file", plugin_uri=uri, file_type=file_type)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            # Assume the response contains file content
            # For now, return empty content
            return Response(content="", media_type="text/plain")
        else:
            return Response(content="", media_type="text/plain")
    except asyncio.TimeoutError:
        logger.warning("get_plugin_file timed out")
        return Response(content="", media_type="text/plain")
    except Exception as exc:
        logger.exception("Error calling get_plugin_file: %s", exc)
        return Response(content="", media_type="text/plain")


@router.get("/file/custom")
async def get_plugin_custom_file(
    request: Request,
    filename: str = Query(..., description="Relative filename"),
    uri: str = Query(..., description="Plugin URI")
):
    """Get custom plugin GUI assets (images, WASM, etc.)."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return Response(content=b"", media_type="application/octet-stream")

    try:
        fut = zmq_client.call("session_manager", "get_plugin_custom_file", plugin_uri=uri, filename=filename)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            # Assume the response contains file content
            # For now, return empty content
            return Response(content=b"", media_type="application/octet-stream")
        else:
            return Response(content=b"", media_type="application/octet-stream")
    except asyncio.TimeoutError:
        logger.warning("get_plugin_custom_file timed out")
        return Response(content=b"", media_type="application/octet-stream")
    except Exception as exc:
        logger.exception("Error calling get_plugin_custom_file: %s", exc)
        return Response(content=b"", media_type="application/octet-stream")


@router.post("/install")
async def install_plugin(request: Request, file: UploadFile = File(...)):
    """Install a plugin package from uploaded bundle file."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {
            "ok": False,
            "installed": [],
            "removed": [],
            "error": "ZMQ client not available"
        }

    try:
        # Read the uploaded file content
        file_content = await file.read()
        
        # For now, this would need to be implemented to handle file upload and installation
        # The handler would need to accept file data
        return {
            "ok": False,
            "installed": [],
            "removed": [],
            "error": "Plugin installation not implemented"
        }
    except Exception as exc:
        logger.exception("Error installing plugin: %s", exc)
        return {
            "ok": False,
            "installed": [],
            "removed": [],
            "error": str(exc)
        }