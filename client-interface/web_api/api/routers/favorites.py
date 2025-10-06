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
    """Add a plugin to user's favorites list"""
    # Call session manager to add favorite
    return {"ok": False}


@router.post("/remove")
async def remove_favorite(
    uri: str = Form(..., description="Plugin URI")
):
    """Remove a plugin from user's favorites list"""
    # Call session manager to remove favorite
    return {"ok": False}