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
    """NOT IMPLEMENTED: Save current plugin parameter states as a snapshot.

    TODO: ask session manager to capture current parameter values and persist snapshot data.
    """
    # Call session manager to save current state as snapshot
    return {"ok": False}


@router.get("/saveas")
async def save_snapshot_as(
    title: str = Query(..., description="Snapshot title")
):
    """NOT IMPLEMENTED: Save current state as a new named snapshot.

    TODO: delegate to session manager snapshot_saveas and return id/title.
    """
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
    """NOT IMPLEMENTED: Change the name of an existing snapshot.

    TODO: call session manager to update snapshot TTL metadata.
    """
    # Call session manager to rename snapshot
    return SnapshotRenameResponse(
        ok=False,
        title=title
    )


@router.get("/remove")
async def remove_snapshot(
    id: int = Query(..., description="Snapshot ID")
):
    """NOT IMPLEMENTED: Delete a snapshot.

    TODO: instruct session manager to remove snapshot data from the pedalboard bundle.
    """
    # Call session manager to remove snapshot
    return {"ok": False}


@router.get("/list")
async def list_snapshots():
    """NOT IMPLEMENTED: Get all snapshots for current pedalboard.

    TODO: request snapshot list from session manager and return id->name mapping.
    """
    # Call session manager for snapshot list
    return {
        "0": "Default"
    }


@router.get("/name")
async def get_snapshot_name(
    id: int = Query(..., description="Snapshot ID")
):
    """NOT IMPLEMENTED: Get the name of a specific snapshot.

    TODO: use session manager to lookup the snapshot name by ID.
    """
    # Call session manager for snapshot name
    return SnapshotNameResponse(
        ok=False,
        name=""
    )


@router.get("/load")
async def load_snapshot(
    id: int = Query(..., description="Snapshot ID")
):
    """NOT IMPLEMENTED: Load a snapshot, restoring all parameter values.

    TODO: instruct session manager to apply saved parameter values and broadcast param_set messages.
    """
    # Call session manager to load snapshot
    return {"ok": False}