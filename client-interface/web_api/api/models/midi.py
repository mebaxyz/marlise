from typing import Dict, List
from pydantic import BaseModel


class MidiDevice(BaseModel):
    device_id: str
    name: str


class MidiDevicesResponse(BaseModel):
    devsInUse: List[str]
    devList: List[str]
    names: Dict[str, str]
    midiAggregatedMode: bool


class MidiDevicesRequest(BaseModel):
    devs: List[str]
    midiAggregatedMode: bool
    midiLoopback: bool = False
