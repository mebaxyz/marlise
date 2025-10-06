"""
Banks (Pedalboard Collections) related API endpoints
"""
from typing import List
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..models import Bank, BankSaveRequest, StatusResponse

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=List[Bank])
async def get_banks():
    """Get organized collections of pedalboards grouped into banks"""
    # Call session manager for banks list
    return []


@router.post("/save")
async def save_banks(request: BankSaveRequest):
    """Save bank organization and pedalboard groupings"""
    # Call session manager to save banks configuration
    return {"ok": False}