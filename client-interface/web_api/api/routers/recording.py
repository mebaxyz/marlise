"""
Recording and Sharing related API endpoints
"""
from fastapi import APIRouter, Form

from ..models import RecordingDownloadResponse, UserIdSaveRequest, StatusResponse

from ..main import zmq_client
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recording", tags=["recording"])


@router.get("/start")
async def start_recording():
    """Start recording audio from the current pedalboard.

    TODO: instruct session manager to begin recording and return immediate status.
    """
    # Call session manager to start recording
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "start_recording")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("start_recording timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling start_recording: %s", exc)
        return {"ok": False}


@router.get("/stop")
async def stop_recording():
    """Stop audio recording and finalize the file.

    TODO: instruct session manager to stop recording and finalize temporary audio file.
    """
    # Call session manager to stop recording
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "stop_recording")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("stop_recording timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling stop_recording: %s", exc)
        return {"ok": False}


@router.get("/play/start")
async def start_playback():
    """Start playback of the recorded audio.

    TODO: request session manager to start playback (mute live audio as needed).
    """
    # Call session manager to start playback
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "start_playback")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("start_playback timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling start_playback: %s", exc)
        return {"ok": False}


@router.get("/play/wait")
async def wait_playback():
    """Wait for playback to complete.

    TODO: request session manager to wait for playback completion.
    """
    # Call session manager to wait for playback
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "wait_playback")
        resp = await asyncio.wait_for(fut, timeout=30.0)  # Longer timeout for playback
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("wait_playback timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling wait_playback: %s", exc)
        return {"ok": False}


@router.get("/play/stop")
async def stop_playback():
    """Stop audio playback immediately.

    TODO: instruct session manager to stop playback and restore live audio.
    """
    # Call session manager to stop playback
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "stop_playback")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("stop_playback timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling stop_playback: %s", exc)
        return {"ok": False}


@router.get("/download")
async def download_recording():
    """Download the recorded audio file.

    TODO: obtain audio file from session manager, base64-encode and return.
    """
    # Call session manager to get recorded audio
    if zmq_client is None:
        return RecordingDownloadResponse(ok=False, audio="")

    try:
        fut = zmq_client.call("session_manager", "download_recording")
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for file transfer
        if isinstance(resp, dict) and resp.get("success", False):
            return RecordingDownloadResponse(ok=True, audio=resp.get("audio", ""))
        else:
            return RecordingDownloadResponse(ok=False, audio="")
    except asyncio.TimeoutError:
        logger.warning("download_recording timed out")
        return RecordingDownloadResponse(ok=False, audio="")
    except Exception as exc:
        logger.exception("Error calling download_recording: %s", exc)
        return RecordingDownloadResponse(ok=False, audio="")


@router.get("/reset")
async def reset_recording():
    """Clear/delete the current recording.

    TODO: instruct session manager to delete temporary recording file and reset state.
    """
    # Call session manager to reset recording
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "reset_recording")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("reset_recording timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling reset_recording: %s", exc)
        return {"ok": False}


# Note: save_user_id endpoint is in misc.py router instead