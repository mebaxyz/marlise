from typing import Any
from pydantic import BaseModel


class ConfigSetRequest(BaseModel):
    key: str
    value: Any


class ConfigGetResponse(BaseModel):
    value: Any
