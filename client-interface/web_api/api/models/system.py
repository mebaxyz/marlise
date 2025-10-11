from pydantic import BaseModel


class PingResponse(BaseModel):
    ihm_online: bool
    ihm_time: float


class TrueBypassRequest(BaseModel):
    channel: str  # "Left" or "Right"
    enabled: bool


class BufferSizeRequest(BaseModel):
    size: int  # 128 or 256


class BufferSizeResponse(BaseModel):
    ok: bool
    size: int
