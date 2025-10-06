from typing import Dict
from pydantic import BaseModel


# Snapshot Models
class SnapshotSaveAsRequest(BaseModel):
    title: str


class SnapshotSaveAsResponse(BaseModel):
    ok: bool
    id: int
    title: str


class SnapshotRenameRequest(BaseModel):
    id: int
    title: str


class SnapshotRenameResponse(BaseModel):
    ok: bool
    title: str


class SnapshotNameResponse(BaseModel):
    ok: bool
    name: str


class SnapshotListResponse(BaseModel):
    snapshots: Dict[str, str]  # id -> name mapping
