"""
File System and User Files API endpoints
"""
from typing import List
from fastapi import APIRouter, Query

from ..models import FileListResponse, UserFile

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/list", response_model=FileListResponse)
async def list_user_files(
    types: str = Query(..., description="Comma-separated file types: audioloop,audiorecording,audiosample,audiotrack,cabsim,h2drumkit,ir,midiclip,midisong,sf2,sfz,aidadspmodel,nammodel")
):
    """List user files of specific types for plugin file selectors"""
    # Parse comma-separated types
    file_types = [t.strip() for t in types.split(',')]
    
    # Call session manager to scan for user files
    return FileListResponse(
        ok=False,
        files=[]
    )