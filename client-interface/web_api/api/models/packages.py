from typing import List, Optional
from pydantic import BaseModel


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
