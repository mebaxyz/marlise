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
    """NOT IMPLEMENTED: Get organized collections of pedalboards grouped into banks.

    TODO: return bank structure sourced from session manager or user preferences.
    """
    return []


@router.post("/save")
async def save_banks(request: BankSaveRequest):
    """Save bank organization and pedalboard groupings"""
    """NOT IMPLEMENTED: Save bank organization and pedalboard groupings.

    TODO: delegate to session manager or preferences store to persist bank config.
    """
    return {"ok": False}