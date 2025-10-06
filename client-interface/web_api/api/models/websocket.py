from typing import Any, Dict
from pydantic import BaseModel


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
