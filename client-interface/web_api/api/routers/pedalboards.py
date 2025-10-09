"""
Pedalboard related API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Form, File, UploadFile, Request
from fastapi.responses import Response

from ..models import (
    PedalboardInfo, PedalboardSaveRequest, PedalboardSaveResponse,
    PedalboardLoadRequest, PedalboardLoadResponse, PedalboardCopyRequest,
    PedalboardRemoveRequest, PedalboardImageResponse, PedalboardDetailInfo,
    CVPortAddRequest, CVPortAddResponse, CVPortRemoveRequest,
    TransportSyncModeRequest, StatusResponse
)

import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pedalboard", tags=["pedalboards"])


@router.get("/list", response_model=List[PedalboardInfo])
async def get_pedalboard_list(request: Request):
    """Get list of all available pedalboards.

    TODO: integrate with session manager to return pedalboard metadata and include default PB.
    """
    # Call session manager for pedalboard list
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return []

    try:
        fut = zmq_client.call("session_manager", "get_pedalboard_list")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return resp.get("pedalboards", [])
        else:
            raise HTTPException(status_code=500, detail=resp.get("error", "Failed to get pedalboard list"))
    except asyncio.TimeoutError:
        logger.warning("get_pedalboard_list timed out")
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        logger.exception("Error calling get_pedalboard_list: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", response_model=PedalboardSaveResponse)
async def save_pedalboard(
    request: Request,
    title: str = Form(...),
    asNew: int = Form(0)
):
    """Save current pedalboard state to file.

    TODO: forward save request to session manager which will persist the .pedalboard bundle.
    """
    # Call session manager to save pedalboard
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardSaveResponse(ok=False, bundlepath=None, title=title)

    try:
        fut = zmq_client.call("session_manager", "save_current_pedalboard", title=title, as_new=asNew)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardSaveResponse(
                ok=True,
                bundlepath=resp.get("bundlepath"),
                title=title
            )
        else:
            return PedalboardSaveResponse(ok=False, bundlepath=None, title=title)
    except asyncio.TimeoutError:
        logger.warning("save_current_pedalboard timed out")
        return PedalboardSaveResponse(ok=False, bundlepath=None, title=title)
    except Exception as exc:
        logger.exception("Error calling save_current_pedalboard: %s", exc)
        return PedalboardSaveResponse(ok=False, bundlepath=None, title=title)


@router.get("/pack_bundle")
async def pack_pedalboard_bundle(
    request: Request,
    bundlepath: str = Query(..., description="Absolute path to pedalboard bundle")
):
    """Download pedalboard as compressed bundle for sharing.

    TODO: stream tar.gz created by session manager or filesystem compressor.
    """
    # Return tar.gz file
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return Response(content=b"", media_type="application/gzip", headers={"Content-Disposition": "attachment; filename=pedalboard.tar.gz"})

    try:
        fut = zmq_client.call("session_manager", "pack_pedalboard_bundle", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for file operations
        if isinstance(resp, dict) and resp.get("success"):
            # Assume the handler returns file data
            file_data = resp.get("file_data", b"")
            filename = resp.get("filename", "pedalboard.tar.gz")
            return Response(
                content=file_data,
                media_type="application/gzip",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return Response(content=b"", media_type="application/gzip", headers={"Content-Disposition": "attachment; filename=pedalboard.tar.gz"})
    except asyncio.TimeoutError:
        logger.warning("pack_pedalboard_bundle timed out")
        return Response(content=b"", media_type="application/gzip", headers={"Content-Disposition": "attachment; filename=pedalboard.tar.gz"})
    except Exception as exc:
        logger.exception("Error calling pack_pedalboard_bundle: %s", exc)
        return Response(content=b"", media_type="application/gzip", headers={"Content-Disposition": "attachment; filename=pedalboard.tar.gz"})


@router.post("/load_bundle", response_model=PedalboardLoadResponse)
async def load_pedalboard_bundle(
    request: Request,
    bundlepath: str = Form(...),
    isDefault: str = Form("0")
):
    """Load a pedalboard from file path into current session.

    TODO: pass bundlepath to session manager to perform the load and emit websocket events.
    """
    # Call session manager to load pedalboard
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardLoadResponse(ok=False, name="")

    try:
        fut = zmq_client.call("session_manager", "load_pedalboard_bundle", bundlepath=bundlepath, is_default=isDefault)
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for file operations
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardLoadResponse(ok=True, name=resp.get("name", ""))
        else:
            return PedalboardLoadResponse(ok=False, name="")
    except asyncio.TimeoutError:
        logger.warning("load_pedalboard_bundle timed out")
        return PedalboardLoadResponse(ok=False, name="")
    except Exception as exc:
        logger.exception("Error calling load_pedalboard_bundle: %s", exc)
        return PedalboardLoadResponse(ok=False, name="")


@router.post("/load_web", response_model=PedalboardLoadResponse)
async def load_pedalboard_web(request: Request, file: UploadFile = File(...)):
    """Upload and load a pedalboard bundle from file upload.

    TODO: accept multipart upload, store temp file, ask session manager to extract and load.
    """
    # Process uploaded pedalboard file
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardLoadResponse(ok=False, name="")

    try:
        # Read file content
        file_data = await file.read()
        filename = file.filename

        fut = zmq_client.call("session_manager", "load_pedalboard_web", file_data=file_data, filename=filename)
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for file operations
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardLoadResponse(ok=True, name=resp.get("name", ""))
        else:
            return PedalboardLoadResponse(ok=False, name="")
    except asyncio.TimeoutError:
        logger.warning("load_pedalboard_web timed out")
        return PedalboardLoadResponse(ok=False, name="")
    except Exception as exc:
        logger.exception("Error calling load_pedalboard_web: %s", exc)
        return PedalboardLoadResponse(ok=False, name="")


@router.get("/factorycopy")
async def factory_copy_pedalboard(
    request: Request,
    bundlepath: str = Query(..., description="Factory pedalboard path"),
    title: str = Query(..., description="New pedalboard title")
):
    """Create a user copy of a factory/read-only pedalboard.

    TODO: instruct session manager to copy factory PB into user's pedalboards dir.
    """
    # Call session manager to copy factory pedalboard
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False, "bundlepath": "", "title": title, "plugins": [], "connections": []}

    try:
        fut = zmq_client.call("session_manager", "factory_copy_pedalboard", bundlepath=bundlepath, title=title)
        resp = await asyncio.wait_for(fut, timeout=5.0)
        if isinstance(resp, dict) and resp.get("success"):
            return {
                "ok": True,
                "bundlepath": resp.get("bundlepath", ""),
                "title": title,
                "plugins": resp.get("plugins", []),
                "connections": resp.get("connections", [])
            }
        else:
            return {"ok": False, "bundlepath": "", "title": title, "plugins": [], "connections": []}
    except asyncio.TimeoutError:
        logger.warning("factory_copy_pedalboard timed out")
        return {"ok": False, "bundlepath": "", "title": title, "plugins": [], "connections": []}
    except Exception as exc:
        logger.exception("Error calling factory_copy_pedalboard: %s", exc)
        return {"ok": False, "bundlepath": "", "title": title, "plugins": [], "connections": []}


@router.get("/info")
async def get_pedalboard_info(
    request: Request,
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Get detailed pedalboard information without loading it.

    TODO: parse the .pedalboard TTL files (or request session manager helper) and return metadata.
    """
    # Call session manager for pedalboard info
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardDetailInfo(title="", plugins=[], connections=[], hardware={})

    try:
        fut = zmq_client.call("session_manager", "get_pedalboard_info", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardDetailInfo(
                title=resp.get("title", ""),
                plugins=resp.get("plugins", []),
                connections=resp.get("connections", []),
                hardware=resp.get("hardware", {})
            )
        else:
            return PedalboardDetailInfo(title="", plugins=[], connections=[], hardware={})
    except asyncio.TimeoutError:
        logger.warning("get_pedalboard_info timed out")
        return PedalboardDetailInfo(title="", plugins=[], connections=[], hardware={})
    except Exception as exc:
        logger.exception("Error calling get_pedalboard_info: %s", exc)
        return PedalboardDetailInfo(title="", plugins=[], connections=[], hardware={})


@router.get("/remove")
async def remove_pedalboard(
    request: Request,
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Delete a pedalboard from the filesystem.

    TODO: delegate deletion to session manager to ensure safe removal and notify clients.
    """
    # Call session manager to remove pedalboard
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "remove_pedalboard", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("remove_pedalboard timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling remove_pedalboard: %s", exc)
        return {"ok": False}


@router.get("/image/{image_type}.png")
async def get_pedalboard_image(
    request: Request,
    image_type: str,  # screenshot or thumbnail
    bundlepath: str = Query(..., description="Pedalboard bundle path"),
    tstamp: Optional[str] = Query(None, description="Timestamp for cache busting"),
    v: Optional[str] = Query(None, description="Version for cache busting")
):
    """Get pedalboard screenshot or thumbnail image.

    TODO: serve screenshot.png/thumbnail.png from bundle or return default image.
    """
    # Return pedalboard image
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return Response(content=b"", media_type="image/png")

    try:
        fut = zmq_client.call("session_manager", "get_pedalboard_image", bundlepath=bundlepath, image_type=image_type)
        resp = await asyncio.wait_for(fut, timeout=5.0)
        if isinstance(resp, dict) and resp.get("success"):
            image_data = resp.get("image_data", b"")
            return Response(content=image_data, media_type="image/png")
        else:
            return Response(content=b"", media_type="image/png")
    except asyncio.TimeoutError:
        logger.warning("get_pedalboard_image timed out")
        return Response(content=b"", media_type="image/png")
    except Exception as exc:
        logger.exception("Error calling get_pedalboard_image: %s", exc)
        return Response(content=b"", media_type="image/png")


@router.get("/image/generate")
async def generate_pedalboard_image(
    request: Request,
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Trigger asynchronous generation of pedalboard screenshot.

    TODO: schedule screenshot generation via session manager and return immediate status.
    """
    # Start screenshot generation
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardImageResponse(ok=False, ctime="0")

    try:
        fut = zmq_client.call("session_manager", "generate_pedalboard_image", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardImageResponse(ok=True, ctime=resp.get("ctime", "0"))
        else:
            return PedalboardImageResponse(ok=False, ctime="0")
    except asyncio.TimeoutError:
        logger.warning("generate_pedalboard_image timed out")
        return PedalboardImageResponse(ok=False, ctime="0")
    except Exception as exc:
        logger.exception("Error calling generate_pedalboard_image: %s", exc)
        return PedalboardImageResponse(ok=False, ctime="0")


@router.get("/image/wait")
async def wait_pedalboard_image(
    request: Request,
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Wait for screenshot generation to complete.

    TODO: poll session manager for generation completion and return final ctime.
    """
    # Wait for screenshot completion
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return PedalboardImageResponse(ok=False, ctime="0")

    try:
        fut = zmq_client.call("session_manager", "wait_pedalboard_image", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=30.0)  # Longer timeout for waiting
        if isinstance(resp, dict) and resp.get("success"):
            return PedalboardImageResponse(ok=True, ctime=resp.get("ctime", "0"))
        else:
            return PedalboardImageResponse(ok=False, ctime="0")
    except asyncio.TimeoutError:
        logger.warning("wait_pedalboard_image timed out")
        return PedalboardImageResponse(ok=False, ctime="0")
    except Exception as exc:
        logger.exception("Error calling wait_pedalboard_image: %s", exc)
        return PedalboardImageResponse(ok=False, ctime="0")


@router.get("/image/check")
async def check_pedalboard_image(
    request: Request,
    bundlepath: str = Query(..., description="Pedalboard bundle path"),
    v: Optional[str] = Query(None, description="Version parameter")
):
    """Check screenshot generation status.

    TODO: return {status, ctime} by querying generation state.
    """
    # Check screenshot status
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"status": 0, "ctime": "0"}

    try:
        fut = zmq_client.call("session_manager", "check_pedalboard_image", bundlepath=bundlepath)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return {"status": resp.get("status", 0), "ctime": resp.get("ctime", "0")}
        else:
            return {"status": 0, "ctime": "0"}
    except asyncio.TimeoutError:
        logger.warning("check_pedalboard_image timed out")
        return {"status": 0, "ctime": "0"}
    except Exception as exc:
        logger.exception("Error calling check_pedalboard_image: %s", exc)
        return {"status": 0, "ctime": "0"}


@router.post("/cv_addressing_plugin_port/add")
async def add_cv_addressing_port(
    request: Request,
    uri: str = Form(...),
    name: str = Form(...)
):
    """Add CV addressing plugin port.

    TODO: call session manager to register CV addressing plugin port.
    """
    # Call session manager to add CV port
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return CVPortAddResponse(ok=False, operational_mode="=")

    try:
        fut = zmq_client.call("session_manager", "add_cv_addressing_port", uri=uri, name=name)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return CVPortAddResponse(ok=True, operational_mode=resp.get("operational_mode", "="))
        else:
            return CVPortAddResponse(ok=False, operational_mode="=")
    except asyncio.TimeoutError:
        logger.warning("add_cv_addressing_port timed out")
        return CVPortAddResponse(ok=False, operational_mode="=")
    except Exception as exc:
        logger.exception("Error calling add_cv_addressing_port: %s", exc)
        return CVPortAddResponse(ok=False, operational_mode="=")


@router.post("/cv_addressing_plugin_port/remove")
async def remove_cv_addressing_port(
    request: Request,
    uri: str = Form(...)
):
    """Remove CV addressing plugin port.

    TODO: instruct session manager to remove CV addressing port mapping.
    """
    # Call session manager to remove CV port
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "remove_cv_addressing_port", uri=uri)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("remove_cv_addressing_port timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling remove_cv_addressing_port: %s", exc)
        return {"ok": False}


@router.post("/transport/set_sync_mode/{mode}")
async def set_transport_sync_mode(
    request: Request,
    mode: str  # none, midi_clock_slave, link
):
    """Set transport synchronization mode.

    TODO: call session manager to change transport sync mode (JACK/midi/link).
    """
    # Call session manager to set sync mode
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "set_transport_sync_mode", mode=mode)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("set_transport_sync_mode timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling set_transport_sync_mode: %s", exc)
        return {"ok": False}