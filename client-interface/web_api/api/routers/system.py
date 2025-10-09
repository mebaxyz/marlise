"""
System, Device, and Performance Control API endpoints
"""
from fastapi import APIRouter, Path, Form, Request

from ..models import (
    PingResponse, TrueBypassRequest, BufferSizeRequest, BufferSizeResponse,
    ConfigSetRequest, ConfigGetResponse, StatusResponse
)

import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ping", response_model=PingResponse)
async def ping_device(request: Request):
    """Check HMI (Hardware Machine Interface) connection status and latency."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        logger.debug("zmq_client not available, returning default ping response")
        return PingResponse(ihm_online=False, ihm_time=0.0)

    try:
        fut = zmq_client.call("session_manager", "ping_hmi")
        resp = await asyncio.wait_for(fut, timeout=2.0)

        if isinstance(resp, dict) and resp.get("success"):
            return PingResponse(
                ihm_online=bool(resp.get("ihm_online", False)),
                ihm_time=float(resp.get("ihm_time", 0.0)),
            )
        else:
            return PingResponse(ihm_online=False, ihm_time=0.0)
    except asyncio.TimeoutError:
        logger.warning("ping_hmi timed out")
        return PingResponse(ihm_online=False, ihm_time=0.0)
    except Exception as exc:
        logger.exception("Error calling ping_hmi: %s", exc)
        return PingResponse(ihm_online=False, ihm_time=0.0)


@router.get("/reset")
async def reset_session(request: Request):
    """Reset current session to empty pedalboard state."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "reset_session")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("reset_session timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling reset_session: %s", exc)
        return {"ok": False}


@router.get("/truebypass/{channel}/{state}")
async def set_truebypass(
    request: Request,
    channel: str = Path(..., description="Left or Right"),
    state: str = Path(..., description="true or false")
):
    """Control hardware true bypass relays for direct audio routing."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        enabled = state.lower() == "true"
        fut = zmq_client.call("session_manager", "set_truebypass", channel=channel, state=enabled)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("set_truebypass timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling set_truebypass: %s", exc)
        return {"ok": False}


@router.post("/set_buffersize/{size}")
async def set_buffer_size(
    request: Request,
    size: int = Path(..., description="Buffer size: 128 or 256")
):
    """Change JACK audio buffer size for latency vs. stability tradeoff."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return BufferSizeResponse(ok=False, size=0)

    try:
        if size not in [128, 256]:
            return BufferSizeResponse(ok=False, size=0)

        fut = zmq_client.call("session_manager", "set_buffer_size", size=size)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return BufferSizeResponse(ok=True, size=size)
        else:
            return BufferSizeResponse(ok=False, size=0)
    except asyncio.TimeoutError:
        logger.warning("set_buffer_size timed out")
        return BufferSizeResponse(ok=False, size=0)
    except Exception as exc:
        logger.exception("Error calling set_buffer_size: %s", exc)
        return BufferSizeResponse(ok=False, size=0)


@router.post("/reset_xruns")
async def reset_xruns(request: Request):
    """Reset JACK audio dropout (xrun) counter to zero."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "reset_xruns")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("reset_xruns timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling reset_xruns: %s", exc)
        return {"ok": False}


@router.post("/switch_cpu_freq")
async def switch_cpu_frequency(request: Request):
    """Toggle CPU frequency scaling between performance and powersave modes."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "switch_cpu_frequency")
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("switch_cpu_frequency timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling switch_cpu_frequency: %s", exc)
        return {"ok": False}


# Configuration endpoints
@router.post("/config/set")
async def set_config(
    request: Request,
    key: str = Form(...),
    value: str = Form(...)
):
    """Save user interface configuration settings."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "set_config", key=key, value=value)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("set_config timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling set_config: %s", exc)
        return {"ok": False}


@router.get("/config/get/{key}")
async def get_config(
    request: Request,
    key: str = Path(..., description="Configuration key")
):
    """Get user interface configuration setting."""
    zmq_client = getattr(request.app.state, "zmq_client", None)
    if zmq_client is None:
        return {"value": None}

    try:
        fut = zmq_client.call("session_manager", "get_config", key=key)
        resp = await asyncio.wait_for(fut, timeout=3.0)
        if isinstance(resp, dict) and resp.get("success"):
            return {"value": resp.get("value")}
        else:
            return {"value": None}
    except asyncio.TimeoutError:
        logger.warning("get_config timed out")
        return {"value": None}
    except Exception as exc:
        logger.exception("Error calling get_config: %s", exc)
        return {"value": None}