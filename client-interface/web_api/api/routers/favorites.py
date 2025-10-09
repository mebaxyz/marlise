"""
Favorites related API endpoints
"""
from fastapi import APIRouter, Form

from ..models import FavoriteRequest, StatusResponse

from fastapi import Request
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/add")
async def add_favorite(
    request: Request,
    uri: str = Form(..., description="Plugin URI")
):
    """Add a plugin to user's favorites list.

    TODO: forward the favorite add request to the session manager and persist in preferences.
    """
    # Call session manager to add favorite
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "add_favorite", uri=uri)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("add_favorite timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling add_favorite: %s", exc)
        return {"ok": False}


@router.post("/remove")
async def remove_favorite(
    request: Request,
    uri: str = Form(..., description="Plugin URI")
):
    """Remove a plugin from user's favorites list.

    TODO: forward the favorite removal to the session manager and update stored preferences.
    """
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "remove_favorite", uri=uri)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("remove_favorite timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling remove_favorite: %s", exc)
        return {"ok": False}