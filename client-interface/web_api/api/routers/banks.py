"""
Banks (Pedalboard Collections) related API endpoints
"""
from typing import List
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..models import Bank, BankSaveRequest, StatusResponse

from ..main import zmq_client
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=List[Bank])
async def get_banks():
    """Get organized collections of pedalboards grouped into banks"""
    """NOT IMPLEMENTED: Get organized collections of pedalboards grouped into banks.

    TODO: return bank structure sourced from session manager or user preferences.
    """
    if zmq_client is None:
        return []

    try:
        fut = zmq_client.call("session_manager", "get_banks")
        resp = await asyncio.wait_for(fut, timeout=5.0)
        if isinstance(resp, dict) and resp.get("success", False):
            return resp.get("banks", [])
        else:
            return []
    except asyncio.TimeoutError:
        logger.warning("get_banks timed out")
        return []
    except Exception as exc:
        logger.exception("Error calling get_banks: %s", exc)
        return []


@router.post("/save")
async def save_banks(request: BankSaveRequest):
    """Save bank organization and pedalboard groupings"""
    """NOT IMPLEMENTED: Save bank organization and pedalboard groupings.

    TODO: delegate to session manager or preferences store to persist bank config.
    """
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "save_banks", banks=request.banks)
        resp = await asyncio.wait_for(fut, timeout=10.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("save_banks timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling save_banks: %s", exc)
        return {"ok": False}