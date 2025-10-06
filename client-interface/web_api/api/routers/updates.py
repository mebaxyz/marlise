"""
System Updates and Package Management API endpoints
"""
from fastapi import APIRouter, File, UploadFile

from ..models import (
    PackageUninstallRequest, PackageUninstallResponse,
    PackageInstallResponse, StatusResponse
)

router = APIRouter(tags=["updates"])


@router.post("/update/begin")
async def begin_update():
    """NOT IMPLEMENTED: Start system update/restore process.

    TODO: trigger the system update flow through the session manager and return immediate status.
    """
    # Call session manager to begin update
    return {"ok": False}


@router.post("/update/download")
async def upload_system_image(file: UploadFile = File(...)):
    """NOT IMPLEMENTED: Upload system image file for firmware update.

    TODO: validate image, stage to temp location and pass to update process via session manager.
    """
    # Process uploaded system image
    return {
        "ok": False,
        "result": False
    }


@router.post("/controlchain/download")
async def upload_controlchain_firmware(file: UploadFile = File(...)):
    """NOT IMPLEMENTED: Upload firmware for Control Chain hardware devices.

    TODO: stage firmware and instruct control chain updater via session manager.
    """
    # Process uploaded Control Chain firmware
    return {
        "ok": False,
        "result": False
    }


@router.post("/controlchain/cancel")
async def cancel_controlchain_update():
    """NOT IMPLEMENTED: Cancel ongoing Control Chain firmware update.

    TODO: notify session manager to cancel update process safely.
    """
    # Cancel Control Chain update
    return {"ok": False}


@router.post("/package/uninstall")
async def uninstall_package(request: PackageUninstallRequest):
    """NOT IMPLEMENTED: Uninstall plugin packages.

    TODO: forward uninstall list to session manager, return removed bundles and errors.
    """
    # Call session manager to uninstall packages
    return PackageUninstallResponse(
        ok=False,
        removed=[],
        error="Not implemented"
    )