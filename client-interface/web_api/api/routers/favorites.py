"""
Favorites related API endpoints
"""
from fastapi import APIRouter, Form

from ..models import FavoriteRequest, StatusResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/add")
async def add_favorite(
    uri: str = Form(..., description="Plugin URI")
):
    """NOT IMPLEMENTED: Add a plugin to user's favorites list.

    TODO: forward the favorite add request to the session manager and persist in preferences.
    """
    # Call session manager to add favorite
    return {"ok": False}


@router.post("/remove")
async def remove_favorite(
    uri: str = Form(..., description="Plugin URI")
):
    """NOT IMPLEMENTED: Remove a plugin from user's favorites list.

    TODO: forward the favorite removal to the session manager and update stored preferences.
    """
    # Call session manager to remove favorite
    return {"ok": False}