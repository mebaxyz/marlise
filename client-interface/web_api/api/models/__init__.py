"""Re-export common Pydantic models for the API.

This package splits the original huge `models.py` into smaller modules while
keeping the same public import surface. Code that used
`from client_interface.web_api.api import models` or
`from client_interface.web_api.api.models import PluginInfo` will continue to
work.
"""
from .common import StatusResponse

from .plugins import (
    PluginInfo,
    PluginPort,
    PluginPreset,
    PluginDetailInfo,
    PluginAddRequest,
    PluginBulkRequest,
    PluginConnectionRequest,
    ParameterSetRequest,
    ParameterAddressRequest,
    PresetRequest,
    PresetDeleteRequest,
)

from .pedalboards import (
    PedalboardInfo,
    PedalboardSaveRequest,
    PedalboardSaveResponse,
    PedalboardLoadRequest,
    PedalboardLoadResponse,
    PedalboardCopyRequest,
    PedalboardRemoveRequest,
    PedalboardImageResponse,
    PedalboardDetailInfo,
)

from .snapshots import (
    SnapshotSaveAsRequest,
    SnapshotSaveAsResponse,
    SnapshotRenameRequest,
    SnapshotRenameResponse,
    SnapshotNameResponse,
    SnapshotListResponse,
)

from .banks import BankPedalboard, Bank, BankSaveRequest
from .favorites import FavoriteRequest
from .recording import RecordingDownloadResponse

from .system import (
    PingResponse,
    TrueBypassRequest,
    BufferSizeRequest,
    BufferSizeResponse,
)

from .midi import MidiDevice, MidiDevicesResponse, MidiDevicesRequest
from .files import UserFile, FileListResponse
from .auth import (
    AuthNonceRequest,
    AuthNonceResponse,
    AuthTokenRequest,
    AuthTokenResponse,
)

from .packages import (
    PackageUninstallRequest,
    PackageUninstallResponse,
    PackageInstallResponse,
)

from .config import ConfigSetRequest, ConfigGetResponse
from .transport import TransportSyncModeRequest
from .cv import CVPortAddRequest, CVPortAddResponse, CVPortRemoveRequest
from .user import UserIdSaveRequest
from .websocket import WebSocketMessage

__all__ = [
    "StatusResponse",

    # plugins
    "PluginInfo",
    "PluginPort",
    "PluginPreset",
    "PluginDetailInfo",
    "PluginAddRequest",
    "PluginBulkRequest",
    "PluginConnectionRequest",
    "ParameterSetRequest",
    "ParameterAddressRequest",
    "PresetRequest",
    "PresetDeleteRequest",

    # pedalboards
    "PedalboardInfo",
    "PedalboardSaveRequest",
    "PedalboardSaveResponse",
    "PedalboardLoadRequest",
    "PedalboardLoadResponse",
    "PedalboardCopyRequest",
    "PedalboardRemoveRequest",
    "PedalboardImageResponse",
    "PedalboardDetailInfo",

    # snapshots
    "SnapshotSaveAsRequest",
    "SnapshotSaveAsResponse",
    "SnapshotRenameRequest",
    "SnapshotRenameResponse",
    "SnapshotNameResponse",
    "SnapshotListResponse",

    # banks, favorites, recording
    "BankPedalboard",
    "Bank",
    "BankSaveRequest",
    "FavoriteRequest",
    "RecordingDownloadResponse",

    # system / device
    "PingResponse",
    "TrueBypassRequest",
    "BufferSizeRequest",
    "BufferSizeResponse",

    # midi
    "MidiDevice",
    "MidiDevicesResponse",
    "MidiDevicesRequest",

    # files
    "UserFile",
    "FileListResponse",

    # auth
    "AuthNonceRequest",
    "AuthNonceResponse",
    "AuthTokenRequest",
    "AuthTokenResponse",

    # packages
    "PackageUninstallRequest",
    "PackageUninstallResponse",
    "PackageInstallResponse",

    # misc
    "ConfigSetRequest",
    "ConfigGetResponse",
    "TransportSyncModeRequest",
    "CVPortAddRequest",
    "CVPortAddResponse",
    "CVPortRemoveRequest",
    "UserIdSaveRequest",
    "WebSocketMessage",
]
