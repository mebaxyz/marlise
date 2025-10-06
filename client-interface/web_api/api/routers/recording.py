"""
Recording and Sharing related API endpoints
"""
from fastapi import APIRouter, Form

from ..models import RecordingDownloadResponse, UserIdSaveRequest, StatusResponse

router = APIRouter(prefix="/recording", tags=["recording"])


@router.get("/start")
async def start_recording():
    """NOT IMPLEMENTED: Start recording audio from the current pedalboard.

    TODO: instruct session manager to begin recording and return immediate status.
    """
    # Call session manager to start recording
    return {"ok": False}


@router.get("/stop")
async def stop_recording():
    """NOT IMPLEMENTED: Stop audio recording and finalize the file.

    TODO: instruct session manager to stop recording and finalize temporary audio file.
    """
    # Call session manager to stop recording
    return {"ok": False}


@router.get("/play/start")
async def start_playback():
    """NOT IMPLEMENTED: Start playback of the recorded audio.

    TODO: request session manager to start playback (mute live audio as needed).
    """
    # Call session manager to start playback
    return {"ok": False}


@router.get("/play/wait")
async def wait_playback():
    """NOT IMPLEMENTED: Wait for audio playback to complete.

    TODO: block or poll session manager until playback has finished, with timeout.
    """
    # Call session manager to wait for playback completion
    return {"ok": False}


@router.get("/play/stop")
async def stop_playback():
    """NOT IMPLEMENTED: Stop audio playback immediately.

    TODO: instruct session manager to stop playback and restore live audio.
    """
    # Call session manager to stop playback
    return {"ok": False}


@router.get("/download")
async def download_recording():
    """NOT IMPLEMENTED: Download the recorded audio file.

    TODO: obtain audio file from session manager, base64-encode and return.
    """
    # Call session manager to get recorded audio
    return RecordingDownloadResponse(
        ok=False,
        audio=""
    )


@router.get("/reset")
async def reset_recording():
    """NOT IMPLEMENTED: Clear/delete the current recording.

    TODO: instruct session manager to delete temporary recording file and reset state.
    """
    # Call session manager to reset recording
    return {"ok": False}


# Note: save_user_id endpoint is in misc.py router instead