"""
MIDI Devices and JACK related API endpoints
"""
from typing import List
from fastapi import APIRouter

from ..models import (
    MidiDevicesResponse, MidiDevicesRequest, StatusResponse
)

router = APIRouter(prefix="/jack", tags=["jack", "midi"])


@router.get("/get_midi_devices", response_model=MidiDevicesResponse)
async def get_midi_devices():
    """NOT IMPLEMENTED: Get list of available MIDI devices and current configuration.

    TODO: query session manager for JACK MIDI ports and aggregated mode.
    """
    # Call session manager for MIDI device info
    return MidiDevicesResponse(
        devsInUse=[],
        devList=[],
        names={},
        midiAggregatedMode=True
    )


@router.post("/set_midi_devices")
async def set_midi_devices(request: MidiDevicesRequest):
    """NOT IMPLEMENTED: Configure which MIDI devices are active and their routing mode.

    TODO: forward configuration to session manager which will create/remove JACK ports.
    """
    # Call session manager to configure MIDI devices
    return {"ok": False}