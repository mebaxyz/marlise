"""
System, Device, and Performance Control API endpoints
"""
from fastapi import APIRouter, Path, Form

from ..models import (
    PingResponse, TrueBypassRequest, BufferSizeRequest, BufferSizeResponse,
    ConfigSetRequest, ConfigGetResponse, StatusResponse
)

from ..main import zmq_client
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ping", response_model=PingResponse)
async def ping_device():
    """NOT IMPLEMENTED: Check HMI (Hardware Machine Interface) connection status and latency.

    TODO: call session manager to test HMI serial communication and measure round-trip time.
    """
    # If ZMQ client is available, ask session manager for ping/HMI health
    if zmq_client is None:
        logger.debug("zmq_client not available, returning default ping response")
        return PingResponse(ihm_online=False, ihm_time=0.0)

    try:
        # The session manager method name is assumed to be 'ping_hmi'. This is
        # a safe, best-effort call; adjust the RPC name if your session manager
        # uses a different method.
        fut = zmq_client.call("session_manager", "ping_hmi")
        # Wait with timeout to avoid hanging request
        resp = await asyncio.wait_for(fut, timeout=2.0)

        # Expecting a dict-like response with keys 'ihm_online' and 'ihm_time'
        if isinstance(resp, dict):
            return PingResponse(
                ihm_online=bool(resp.get("ihm_online", False)),
                ihm_time=float(resp.get("ihm_time", 0.0)),
            )
        # Fallback
        logger.warning("Unexpected ping_hmi response type: %s", type(resp))
        return PingResponse(ihm_online=False, ihm_time=0.0)
    except asyncio.TimeoutError:
        logger.warning("ping_hmi timed out")
        return PingResponse(ihm_online=False, ihm_time=0.0)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error calling ping_hmi: %s", exc)
        return PingResponse(ihm_online=False, ihm_time=0.0)


@router.get("/reset")
async def reset_session():
    """NOT IMPLEMENTED: Reset current session to empty pedalboard state.

    TODO: instruct session manager to clear plugins/connections and load default pedalboard.
    """
    # Call session manager to reset session
    return {"ok": False}


@router.get("/truebypass/{channel}/{state}")
async def set_truebypass(
    channel: str = Path(..., description="Left or Right"),
    state: str = Path(..., description="true or false")
):
    """NOT IMPLEMENTED: Control hardware true bypass relays for direct audio routing.

    TODO: call session manager to toggle truebypass and emit websocket event.
    """
    enabled = state.lower() == "true"
    # Call session manager to set truebypass
    return {"ok": False}


@router.post("/set_buffersize/{size}")
async def set_buffer_size(
    size: int = Path(..., description="Buffer size: 128 or 256")
):
    """NOT IMPLEMENTED: Change JACK audio buffer size for latency vs. stability tradeoff.

    TODO: reconfigure JACK via session manager or host and return new buffer size.
    """
    if size not in [128, 256]:
        return BufferSizeResponse(ok=False, size=0)
    
    # Call session manager to set buffer size
    return BufferSizeResponse(
        ok=False,
        size=size
    )


@router.post("/reset_xruns")
async def reset_xruns():
    """NOT IMPLEMENTED: Reset JACK audio dropout (xrun) counter to zero.

    TODO: call session manager to clear xrun stats and report back.
    """
    # Call session manager to reset xruns
    return {"ok": False}


@router.post("/switch_cpu_freq")
async def switch_cpu_frequency():
    """NOT IMPLEMENTED: Toggle CPU frequency scaling between performance and powersave modes.

    TODO: call session manager to change OS CPU governor and verify state.
    """
    # Call session manager to switch CPU frequency
    return {"ok": False}


# Configuration endpoints
@router.post("/config/set")
async def set_config(
    key: str = Form(...),
    value: str = Form(...)
):
    """NOT IMPLEMENTED: Save user interface configuration settings.

    TODO: persist UI config via session manager/preferences store.
    """
    # Call session manager to set config
    return {"ok": False}


@router.get("/config/get/{key}")
async def get_config(
    key: str = Path(..., description="Configuration key")
):
    """NOT IMPLEMENTED: Get user interface configuration setting.

    TODO: query preferences store via session manager for given key.
    """
    # Call session manager to get config
    return {"value": None}