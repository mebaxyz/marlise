"""
Request and Response models for the MOD UI API
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


# Common Models
class StatusResponse(BaseModel):
    ok: bool
    message: Optional[str] = None


# Plugin Models
class PluginInfo(BaseModel):
    uri: str
    name: str
    category: List[str]
    version: str
    microVersion: int
    minorVersion: int
    release: int
    builder: str


class PluginPort(BaseModel):
    index: int
    name: str
    symbol: str
    ranges: Dict[str, float]
    designation: Optional[str] = None
    properties: List[str] = []


class PluginPreset(BaseModel):
    uri: str
    label: str


class PluginDetailInfo(BaseModel):
    uri: str
    name: str
    ports: Dict[str, Any]
    presets: List[PluginPreset]
    category: List[str]
    microVersion: int
    minorVersion: int
    release: int
    stability: str
    author: Dict[str, str]
    brand: str
    label: str
    license: str
    comment: str
    version: str
    bundles: List[str]
    gui: Dict[str, Any]


class PluginAddRequest(BaseModel):
    uri: str
    x: float = 0.0
    y: float = 0.0


class PluginBulkRequest(BaseModel):
    uris: List[str]


class PluginConnectionRequest(BaseModel):
    from_port: str
    to_port: str


class ParameterSetRequest(BaseModel):
    instance_id: str
    parameter: str
    value: float


class ParameterAddressRequest(BaseModel):
    uri: str
    label: str
    minimum: float
    maximum: float
    value: float
    steps: int = 33
    tempo: bool = False
    dividers: Optional[List[int]] = None
    page: int = 0
    subpage: int = 0
    coloured: bool = False
    momentary: bool = False
    operational_mode: str = "="


class PresetRequest(BaseModel):
    name: str


class PresetDeleteRequest(BaseModel):
    uri: str
    bundle: str


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


# Bank Models
class BankPedalboard(BaseModel):
    title: str
    bundlepath: str
    broken: bool
    hasScreenshot: bool


class Bank(BaseModel):
    title: str
    pedalboards: List[BankPedalboard]


class BankSaveRequest(BaseModel):
    banks: List[Bank]


# Favorites Models
class FavoriteRequest(BaseModel):
    uri: str


# Recording Models
class RecordingDownloadResponse(BaseModel):
    ok: bool
    audio: str  # base64 encoded audio


# Device Models
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


# MIDI Models
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


# File Models
class UserFile(BaseModel):
    fullname: str
    basename: str
    filetype: str


class FileListResponse(BaseModel):
    ok: bool
    files: List[UserFile]


# Authentication Models
class AuthNonceRequest(BaseModel):
    nonce: str
    device_id: Optional[str] = None


class AuthNonceResponse(BaseModel):
    message: str


class AuthTokenRequest(BaseModel):
    token: str
    expires: Optional[int] = None


class AuthTokenResponse(BaseModel):
    access_token: str


# Package Models
class PackageUninstallRequest(BaseModel):
    bundles: List[str]  # absolute paths


class PackageUninstallResponse(BaseModel):
    ok: bool
    removed: List[str]
    error: Optional[str] = None


class PackageInstallResponse(BaseModel):
    ok: bool
    installed: List[str]
    removed: List[str]
    error: Optional[str] = None


# Configuration Models
class ConfigSetRequest(BaseModel):
    key: str
    value: Any


class ConfigGetResponse(BaseModel):
    value: Any


# Transport Models
class TransportSyncModeRequest(BaseModel):
    mode: str  # "none", "midi_clock_slave", "link"


# CV Models
class CVPortAddRequest(BaseModel):
    uri: str
    name: str


class CVPortAddResponse(BaseModel):
    ok: bool
    operational_mode: Union[str, int]


class CVPortRemoveRequest(BaseModel):
    uri: str


# User ID Models
class UserIdSaveRequest(BaseModel):
    name: str
    email: str


# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]