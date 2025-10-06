"""
System, Device, and Performance Control API endpoints
"""
from fastapi import APIRouter, Path, Form

from ..models import (
    PingResponse, TrueBypassRequest, BufferSizeRequest, BufferSizeResponse,
    ConfigSetRequest, ConfigGetResponse, StatusResponse
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ping", response_model=PingResponse)
async def ping_device():
    """Check HMI (Hardware Machine Interface) connection status and latency"""
    # Call session manager to ping HMI
    return PingResponse(
        ihm_online=False,
        ihm_time=0.0
    )


@router.get("/reset")
async def reset_session():
    """Reset current session to empty pedalboard state"""
    # Call session manager to reset session
    return {"ok": False}


@router.get("/truebypass/{channel}/{state}")
async def set_truebypass(
    channel: str = Path(..., description="Left or Right"),
    state: str = Path(..., description="true or false")
):
    """Control hardware true bypass relays for direct audio routing"""
    enabled = state.lower() == "true"
    # Call session manager to set truebypass
    return {"ok": False}


@router.post("/set_buffersize/{size}")
async def set_buffer_size(
    size: int = Path(..., description="Buffer size: 128 or 256")
):
    """Change JACK audio buffer size for latency vs. stability tradeoff"""
    if size not in [128, 256]:
        return BufferSizeResponse(ok=False, size=0)
    
    # Call session manager to set buffer size
    return BufferSizeResponse(
        ok=False,
        size=size
    )


@router.post("/reset_xruns")
async def reset_xruns():
    """Reset JACK audio dropout (xrun) counter to zero"""
    # Call session manager to reset xruns
    return {"ok": False}


@router.post("/switch_cpu_freq")
async def switch_cpu_frequency():
    """Toggle CPU frequency scaling between performance and powersave modes"""
    # Call session manager to switch CPU frequency
    return {"ok": False}


# Configuration endpoints
@router.post("/config/set")
async def set_config(
    key: str = Form(...),
    value: str = Form(...)
):
    """Save user interface configuration settings"""
    # Call session manager to set config
    return {"ok": False}


@router.get("/config/get/{key}")
async def get_config(
    key: str = Path(..., description="Configuration key")
):
    """Get user interface configuration setting"""
    # Call session manager to get config
    return {"value": None}