"""
Pedalboard related API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Form, File, UploadFile
from fastapi.responses import Response

from ..models import (
    PedalboardInfo, PedalboardSaveRequest, PedalboardSaveResponse,
    PedalboardLoadRequest, PedalboardLoadResponse, PedalboardCopyRequest,
    PedalboardRemoveRequest, PedalboardImageResponse, PedalboardDetailInfo,
    CVPortAddRequest, CVPortAddResponse, CVPortRemoveRequest,
    TransportSyncModeRequest, StatusResponse
)

router = APIRouter(prefix="/pedalboard", tags=["pedalboards"])


@router.get("/list", response_model=List[PedalboardInfo])
async def get_pedalboard_list():
    """Get list of all available pedalboards"""
    # Call session manager for pedalboard list
    # Include default pedalboard with title "Default"
    return []


@router.post("/save", response_model=PedalboardSaveResponse)
async def save_pedalboard(
    title: str = Form(...),
    asNew: int = Form(0)
):
    """Save current pedalboard state to file"""
    # Call session manager to save pedalboard
    return PedalboardSaveResponse(
        ok=False,
        bundlepath=None,
        title=title
    )


@router.get("/pack_bundle")
async def pack_pedalboard_bundle(
    bundlepath: str = Query(..., description="Absolute path to pedalboard bundle")
):
    """Download pedalboard as compressed bundle for sharing"""
    # Return tar.gz file
    return Response(
        content=b"", 
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=pedalboard.tar.gz"}
    )


@router.post("/load_bundle", response_model=PedalboardLoadResponse)
async def load_pedalboard_bundle(
    bundlepath: str = Form(...),
    isDefault: str = Form("0")
):
    """Load a pedalboard from file path into current session"""
    # Call session manager to load pedalboard
    return PedalboardLoadResponse(
        ok=False,
        name=""
    )


@router.post("/load_web", response_model=PedalboardLoadResponse)
async def load_pedalboard_web(file: UploadFile = File(...)):
    """Upload and load a pedalboard bundle from file upload"""
    # Process uploaded pedalboard file
    return PedalboardLoadResponse(
        ok=False,
        name=""
    )


@router.get("/factorycopy")
async def factory_copy_pedalboard(
    bundlepath: str = Query(..., description="Factory pedalboard path"),
    title: str = Query(..., description="New pedalboard title")
):
    """Create a user copy of a factory/read-only pedalboard"""
    # Call session manager to copy factory pedalboard
    return {
        "ok": False,
        "bundlepath": "",
        "title": title,
        "plugins": [],
        "connections": []
    }


@router.get("/info")
async def get_pedalboard_info(
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Get detailed pedalboard information without loading it"""
    # Call session manager for pedalboard info
    return PedalboardDetailInfo(
        title="",
        plugins=[],
        connections=[],
        hardware={}
    )


@router.get("/remove")
async def remove_pedalboard(
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Delete a pedalboard from the filesystem"""
    # Call session manager to remove pedalboard
    return {"ok": False}


@router.get("/image/{image_type}.png")
async def get_pedalboard_image(
    image_type: str,  # screenshot or thumbnail
    bundlepath: str = Query(..., description="Pedalboard bundle path"),
    tstamp: Optional[str] = Query(None, description="Timestamp for cache busting"),
    v: Optional[str] = Query(None, description="Version for cache busting")
):
    """Get pedalboard screenshot or thumbnail image"""
    # Return pedalboard image
    return Response(content=b"", media_type="image/png")


@router.get("/image/generate")
async def generate_pedalboard_image(
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Trigger asynchronous generation of pedalboard screenshot"""
    # Start screenshot generation
    return PedalboardImageResponse(
        ok=False,
        ctime="0"
    )


@router.get("/image/wait")
async def wait_pedalboard_image(
    bundlepath: str = Query(..., description="Pedalboard bundle path")
):
    """Wait for screenshot generation to complete"""
    # Wait for screenshot completion
    return PedalboardImageResponse(
        ok=False,
        ctime="0"
    )


@router.get("/image/check")
async def check_pedalboard_image(
    bundlepath: str = Query(..., description="Pedalboard bundle path"),
    v: Optional[str] = Query(None, description="Version parameter")
):
    """Check screenshot generation status"""
    # Check screenshot status
    return {
        "status": 0,
        "ctime": "0"
    }


@router.post("/cv_addressing_plugin_port/add")
async def add_cv_addressing_port(
    uri: str = Form(...),
    name: str = Form(...)
):
    """Add CV addressing plugin port"""
    # Call session manager to add CV port
    return CVPortAddResponse(
        ok=False,
        operational_mode="="
    )


@router.post("/cv_addressing_plugin_port/remove")
async def remove_cv_addressing_port(
    uri: str = Form(...)
):
    """Remove CV addressing plugin port"""
    # Call session manager to remove CV port
    return {"ok": False}


@router.post("/transport/set_sync_mode/{mode}")
async def set_transport_sync_mode(
    mode: str  # none, midi_clock_slave, link
):
    """Set transport synchronization mode"""
    # Call session manager to set sync mode
    return {"ok": False}