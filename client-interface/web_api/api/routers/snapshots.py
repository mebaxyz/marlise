"""
Snapshot (Pedalboard Presets) related API endpoints
"""
from typing import Dict
from fastapi import APIRouter, Query, Path

from ..models import (
    SnapshotSaveAsRequest, SnapshotSaveAsResponse,
    SnapshotRenameRequest, SnapshotRenameResponse,
    SnapshotNameResponse, SnapshotListResponse,
    StatusResponse
)

router = APIRouter(prefix="/snapshot", tags=["snapshots"])


@router.post("/save")
async def save_snapshot():
    """Save current plugin parameter states as a snapshot"""
    # Call session manager to save current state as snapshot
    return {"ok": False}


@router.get("/saveas")
async def save_snapshot_as(
    title: str = Query(..., description="Snapshot title")
):
    """Save current state as a new named snapshot"""
    # Call session manager to save as new snapshot
    return SnapshotSaveAsResponse(
        ok=False,
        id=0,
        title=title
    )


@router.get("/rename")
async def rename_snapshot(
    id: int = Query(..., description="Snapshot ID"),
    title: str = Query(..., description="New snapshot title")
):
    """Change the name of an existing snapshot"""
    # Call session manager to rename snapshot
    return SnapshotRenameResponse(
        ok=False,
        title=title
    )


@router.get("/remove")
async def remove_snapshot(
    id: int = Query(..., description="Snapshot ID")
):
    """Delete a snapshot"""
    # Call session manager to remove snapshot
    return {"ok": False}


@router.get("/list")
async def list_snapshots():
    """Get all snapshots for current pedalboard"""
    # Call session manager for snapshot list
    return {
        "0": "Default"
    }


@router.get("/name")
async def get_snapshot_name(
    id: int = Query(..., description="Snapshot ID")
):
    """Get the name of a specific snapshot"""
    # Call session manager for snapshot name
    return SnapshotNameResponse(
        ok=False,
        name=""
    )


@router.get("/load")
async def load_snapshot(
    id: int = Query(..., description="Snapshot ID")
):
    """Load a snapshot, restoring all parameter values"""
    # Call session manager to load snapshot
    return {"ok": False}