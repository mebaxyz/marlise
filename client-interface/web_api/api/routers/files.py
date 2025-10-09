"""
File System and User Files API endpoints
"""
from typing import List
from fastapi import APIRouter, Query

from ..models import FileListResponse, UserFile

from fastapi import Request
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/list", response_model=FileListResponse)
async def list_user_files(
    request: Request,
    types: str = Query(..., description="Comma-separated file types: audioloop,audiorecording,audiosample,audiotrack,cabsim,h2drumkit,ir,midiclip,midisong,sf2,sfz,aidadspmodel,nammodel"),
):
    """List user files of specific types for plugin file selectors.

    TODO: parse requested types and ask session manager to scan user directories for matching files.
    """
    # Parse comma-separated types
    file_types = [t.strip() for t in types.split(',')]
    
    # Call session manager to scan for user files
    # Get zmq_client from app state
    zmq_client = getattr(request.app.state, 'zmq_client', None) if request is not None else None
    if zmq_client is None:
        return FileListResponse(
            ok=False,
            files=[]
        )

    try:
        fut = zmq_client.call("session_manager", "list_user_files", file_types=file_types)
        resp = await asyncio.wait_for(fut, timeout=10.0)  # File scanning can take time
        if isinstance(resp, dict) and resp.get("success", False):
            return FileListResponse(
                ok=True,
                files=resp.get("files", [])
            )
        else:
            return FileListResponse(
                ok=False,
                files=[]
            )
    except asyncio.TimeoutError:
        logger.warning("list_user_files timed out")
        return FileListResponse(
            ok=False,
            files=[]
        )
    except Exception as exc:
        logger.exception("Error calling list_user_files: %s", exc)
        return FileListResponse(
            ok=False,
            files=[]
        )