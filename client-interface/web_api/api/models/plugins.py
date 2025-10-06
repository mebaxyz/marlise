from typing import Any, Dict, List, Optional
from pydantic import BaseModel


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
