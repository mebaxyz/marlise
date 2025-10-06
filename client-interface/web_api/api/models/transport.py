from pydantic import BaseModel


class TransportSyncModeRequest(BaseModel):
    mode: str  # "none", "midi_clock_slave", "link"
