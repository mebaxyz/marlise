from typing import Optional
from pydantic import BaseModel


class StatusResponse(BaseModel):
    ok: bool
    message: Optional[str] = None
