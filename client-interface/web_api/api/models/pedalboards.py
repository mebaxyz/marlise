from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# Pedalboard Models
class PedalboardInfo(BaseModel):
    title: str
    bundlepath: str
    broken: bool
    factory: bool
    hasScreenshot: bool


class PedalboardSaveRequest(BaseModel):
    title: str
    asNew: bool = False


class PedalboardSaveResponse(BaseModel):
    ok: bool
    bundlepath: Optional[str] = None
    title: str


class PedalboardLoadRequest(BaseModel):
    bundlepath: str
    isDefault: bool = False


class PedalboardLoadResponse(BaseModel):
    ok: bool
    name: str


class PedalboardCopyRequest(BaseModel):
    bundlepath: str
    title: str


class PedalboardRemoveRequest(BaseModel):
    bundlepath: str


class PedalboardImageResponse(BaseModel):
    ok: bool
    ctime: str


class PedalboardDetailInfo(BaseModel):
    title: str
    plugins: List[Dict[str, Any]]
    connections: List[List[str]]
    hardware: Dict[str, Any]
    width: int = 0
    height: int = 0
