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
    """Get list of available MIDI devices and current configuration"""
    # Call session manager for MIDI device info
    return MidiDevicesResponse(
        devsInUse=[],
        devList=[],
        names={},
        midiAggregatedMode=True
    )


@router.post("/set_midi_devices")
async def set_midi_devices(request: MidiDevicesRequest):
    """Configure which MIDI devices are active and their routing mode"""
    # Call session manager to configure MIDI devices
    return {"ok": False}