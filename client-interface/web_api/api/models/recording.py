from pydantic import BaseModel


class RecordingDownloadResponse(BaseModel):
    ok: bool
    audio: str  # base64 encoded audio
