"""
MIDI Devices and JACK related API endpoints
"""
from typing import List
from fastapi import APIRouter

from ..models import (
    MidiDevicesResponse, MidiDevicesRequest, StatusResponse
)

from fastapi import Request
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jack", tags=["jack", "midi"])


@router.get("/get_midi_devices", response_model=MidiDevicesResponse)
async def get_midi_devices(request: Request):
    """Get list of available MIDI devices and current configuration.

    TODO: query session manager for JACK MIDI ports and aggregated mode.
    """
    # Call session manager for MIDI device info
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return MidiDevicesResponse(
            devsInUse=[],
            devList=[],
            names={},
            midiAggregatedMode=True
        )

    try:
        fut = zmq_client.call("session_manager", "get_midi_devices")
        resp = await asyncio.wait_for(fut, timeout=5.0)
        if isinstance(resp, dict) and resp.get("success", False):
            return MidiDevicesResponse(
                devsInUse=resp.get("devs_in_use", []),
                devList=resp.get("dev_list", []),
                names=resp.get("names", {}),
                midiAggregatedMode=resp.get("midi_aggregated_mode", True)
            )
        else:
            return MidiDevicesResponse(
                devsInUse=[],
                devList=[],
                names={},
                midiAggregatedMode=True
            )
    except asyncio.TimeoutError:
        logger.warning("get_midi_devices timed out")
        return MidiDevicesResponse(
            devsInUse=[],
            devList=[],
            names={},
            midiAggregatedMode=True
        )
    except Exception as exc:
        logger.exception("Error calling get_midi_devices: %s", exc)
        return MidiDevicesResponse(
            devsInUse=[],
            devList=[],
            names={},
            midiAggregatedMode=True
        )


@router.post("/set_midi_devices")
async def set_midi_devices(request: Request, payload: MidiDevicesRequest):
    """Configure which MIDI devices are active and their routing mode.

    TODO: forward configuration to session manager which will create/remove JACK ports.
    """
    # Call session manager to configure MIDI devices
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "set_midi_devices",
                     devs_in_use=payload.devs,
                     midi_aggregated_mode=payload.midiAggregatedMode)
        resp = await asyncio.wait_for(fut, timeout=10.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("set_midi_devices timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling set_midi_devices: %s", exc)
        return {"ok": False}