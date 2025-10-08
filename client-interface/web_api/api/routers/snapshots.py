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

from ..main import zmq_client
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/snapshot", tags=["snapshots"])


@router.post("/save")
async def save_snapshot():
    """Save current plugin parameter states as a snapshot.

    TODO: ask session manager to capture current parameter values and persist snapshot data.
    """
    # Call session manager to save current state as snapshot
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "save_snapshot")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("save_snapshot timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling save_snapshot: %s", exc)
        return {"ok": False}


@router.get("/saveas")
async def save_snapshot_as(
    title: str = Query(..., description="Snapshot title")
):
    """Save current state as a new named snapshot.

    TODO: delegate to session manager snapshot_saveas and return id/title.
    """
    # Call session manager to save as new snapshot
    if zmq_client is None:
        return SnapshotSaveAsResponse(ok=False, id=0, title=title)

    try:
        fut = zmq_client.call("session_manager", "save_snapshot_as", title=title)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return SnapshotSaveAsResponse(
                ok=True,
                id=resp.get("id", 0),
                title=title
            )
        else:
            return SnapshotSaveAsResponse(ok=False, id=0, title=title)
    except asyncio.TimeoutError:
        logger.warning("save_snapshot_as timed out")
        return SnapshotSaveAsResponse(ok=False, id=0, title=title)
    except Exception as exc:
        logger.exception("Error calling save_snapshot_as: %s", exc)
        return SnapshotSaveAsResponse(ok=False, id=0, title=title)


@router.get("/rename")
async def rename_snapshot(
    snapshot_id: int = Query(..., description="Snapshot ID"),
    title: str = Query(..., description="New snapshot title")
):
    """Change the name of an existing snapshot.

    TODO: call session manager to update snapshot TTL metadata.
    """
    # Call session manager to rename snapshot
    if zmq_client is None:
        return SnapshotRenameResponse(ok=False, title=title)

    try:
        fut = zmq_client.call("session_manager", "rename_snapshot", id=snapshot_id, title=title)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return SnapshotRenameResponse(ok=True, title=title)
        else:
            return SnapshotRenameResponse(ok=False, title=title)
    except asyncio.TimeoutError:
        logger.warning("rename_snapshot timed out")
        return SnapshotRenameResponse(ok=False, title=title)
    except Exception as exc:
        logger.exception("Error calling rename_snapshot: %s", exc)
        return SnapshotRenameResponse(ok=False, title=title)


@router.get("/remove")
async def remove_snapshot(
    snapshot_id: int = Query(..., description="Snapshot ID")
):
    """Delete a snapshot.

    TODO: instruct session manager to remove snapshot data from the pedalboard bundle.
    """
    # Call session manager to remove snapshot
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "remove_snapshot", id=snapshot_id)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("remove_snapshot timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling remove_snapshot: %s", exc)
        return {"ok": False}


@router.get("/list")
async def list_snapshots():
    """Get all snapshots for current pedalboard.

    TODO: request snapshot list from session manager and return id->name mapping.
    """
    # Call session manager for snapshot list
    if zmq_client is None:
        return {"0": "Default"}

    try:
        fut = zmq_client.call("session_manager", "list_snapshots")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return resp.get("snapshots", {"0": "Default"})
        else:
            return {"0": "Default"}
    except asyncio.TimeoutError:
        logger.warning("list_snapshots timed out")
        return {"0": "Default"}
    except Exception as exc:
        logger.exception("Error calling list_snapshots: %s", exc)
        return {"0": "Default"}


@router.get("/name")
async def get_snapshot_name(
    snapshot_id: int = Query(..., description="Snapshot ID")
):
    """Get the name of a specific snapshot.

    TODO: use session manager to lookup the snapshot name by ID.
    """
    # Call session manager for snapshot name
    if zmq_client is None:
        return SnapshotNameResponse(ok=False, name="")

    try:
        fut = zmq_client.call("session_manager", "get_snapshot_name", id=snapshot_id)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return SnapshotNameResponse(ok=True, name=resp.get("name", ""))
        else:
            return SnapshotNameResponse(ok=False, name="")
    except asyncio.TimeoutError:
        logger.warning("get_snapshot_name timed out")
        return SnapshotNameResponse(ok=False, name="")
    except Exception as exc:
        logger.exception("Error calling get_snapshot_name: %s", exc)
        return SnapshotNameResponse(ok=False, name="")


@router.get("/load")
async def load_snapshot(
    snapshot_id: int = Query(..., description="Snapshot ID")
):
    """Load a snapshot, restoring all parameter values.

    TODO: instruct session manager to apply saved parameter values and broadcast param_set messages.
    """
    # Call session manager to load snapshot
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "load_snapshot", id=snapshot_id)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("load_snapshot timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling load_snapshot: %s", exc)
        return {"ok": False}