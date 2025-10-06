"""
Recording and Sharing related API endpoints
"""
from fastapi import APIRouter, Form

from ..models import RecordingDownloadResponse, UserIdSaveRequest, StatusResponse

router = APIRouter(prefix="/recording", tags=["recording"])


@router.get("/start")
async def start_recording():
    """Start recording audio from the current pedalboard"""
    # Call session manager to start recording
    return {"ok": False}


@router.get("/stop")
async def stop_recording():
    """Stop audio recording and finalize the file"""
    # Call session manager to stop recording
    return {"ok": False}


@router.get("/play/start")
async def start_playback():
    """Start playback of the recorded audio"""
    # Call session manager to start playback
    return {"ok": False}


@router.get("/play/wait")
async def wait_playback():
    """Wait for audio playback to complete"""
    # Call session manager to wait for playback completion
    return {"ok": False}


@router.get("/play/stop")
async def stop_playback():
    """Stop audio playback immediately"""
    # Call session manager to stop playback
    return {"ok": False}


@router.get("/download")
async def download_recording():
    """Download the recorded audio file"""
    # Call session manager to get recorded audio
    return RecordingDownloadResponse(
        ok=False,
        audio=""
    )


@router.get("/reset")
async def reset_recording():
    """Clear/delete the current recording"""
    # Call session manager to reset recording
    return {"ok": False}


# Note: save_user_id endpoint is in misc.py router instead