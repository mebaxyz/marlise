from typing import Union
from pydantic import BaseModel


class CVPortAddRequest(BaseModel):
    uri: str
    name: str


class CVPortAddResponse(BaseModel):
    ok: bool
    operational_mode: Union[str, int]


class CVPortRemoveRequest(BaseModel):
    uri: str
