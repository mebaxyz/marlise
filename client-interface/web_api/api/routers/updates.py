"""
System Updates and Package Management API endpoints
"""
from fastapi import APIRouter, File, UploadFile

from ..models import (
    PackageUninstallRequest, PackageUninstallResponse,
    PackageInstallResponse, StatusResponse
)

from ..main import zmq_client
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["updates"])


@router.post("/update/begin")
async def begin_update():
    """Start system update/restore process.

    TODO: trigger the system update flow through the session manager and return immediate status.
    """
    # Call session manager to begin update
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "begin_update")
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for update process
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("begin_update timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling begin_update: %s", exc)
        return {"ok": False}


@router.post("/update/download")
async def upload_system_image(file: UploadFile = File(...)):
    """Upload system image file for firmware update.

    TODO: validate image, stage to temp location and pass to update process via session manager.
    """
    # Process uploaded system image
    if zmq_client is None:
        return {
            "ok": False,
            "result": False
        }

    try:
        # Read file content
        file_data = await file.read()
        filename = file.filename

        fut = zmq_client.call("session_manager", "upload_system_image", file_data=file_data, filename=filename)
        resp = await asyncio.wait_for(fut, timeout=30.0)  # Longer timeout for file upload
        return {
            "ok": isinstance(resp, dict) and resp.get("success", False),
            "result": isinstance(resp, dict) and resp.get("success", False)
        }
    except asyncio.TimeoutError:
        logger.warning("upload_system_image timed out")
        return {
            "ok": False,
            "result": False
        }
    except Exception as exc:
        logger.exception("Error calling upload_system_image: %s", exc)
        return {
            "ok": False,
            "result": False
        }


@router.post("/controlchain/download")
async def upload_controlchain_firmware(file: UploadFile = File(...)):
    """Upload firmware for Control Chain hardware devices.

    TODO: stage firmware and instruct control chain updater via session manager.
    """
    # Process uploaded Control Chain firmware
    if zmq_client is None:
        return {
            "ok": False,
            "result": False
        }

    try:
        # Read file content
        file_data = await file.read()
        filename = file.filename

        fut = zmq_client.call("session_manager", "upload_controlchain_firmware", file_data=file_data, filename=filename)
        resp = await asyncio.wait_for(fut, timeout=30.0)  # Longer timeout for file upload
        return {
            "ok": isinstance(resp, dict) and resp.get("success", False),
            "result": isinstance(resp, dict) and resp.get("success", False)
        }
    except asyncio.TimeoutError:
        logger.warning("upload_controlchain_firmware timed out")
        return {
            "ok": False,
            "result": False
        }
    except Exception as exc:
        logger.exception("Error calling upload_controlchain_firmware: %s", exc)
        return {
            "ok": False,
            "result": False
        }


@router.post("/controlchain/cancel")
async def cancel_controlchain_update():
    """Cancel ongoing Control Chain firmware update.

    TODO: notify session manager to cancel update process safely.
    """
    # Cancel Control Chain update
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "cancel_controlchain_update")
        resp = await asyncio.wait_for(fut, timeout=10.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("cancel_controlchain_update timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling cancel_controlchain_update: %s", exc)
        return {"ok": False}


@router.post("/package/uninstall")
async def uninstall_package(request: PackageUninstallRequest):
    """Uninstall plugin packages.

    TODO: forward uninstall list to session manager, return removed bundles and errors.
    """
    # Call session manager to uninstall packages
    if zmq_client is None:
        return PackageUninstallResponse(
            ok=False,
            removed=[],
            error="ZMQ client not available"
        )

    try:
        fut = zmq_client.call("session_manager", "uninstall_package", packages=request.bundles)
        resp = await asyncio.wait_for(fut, timeout=30.0)  # Longer timeout for package operations
        if isinstance(resp, dict) and resp.get("success", False):
            return PackageUninstallResponse(
                ok=True,
                removed=resp.get("removed", []),
                error=""
            )
        else:
            return PackageUninstallResponse(
                ok=False,
                removed=[],
                error=resp.get("error", "Uninstall failed") if isinstance(resp, dict) else "Uninstall failed"
            )
    except asyncio.TimeoutError:
        logger.warning("uninstall_package timed out")
        return PackageUninstallResponse(
            ok=False,
            removed=[],
            error="Operation timed out"
        )
    except Exception as exc:
        logger.exception("Error calling uninstall_package: %s", exc)
        return PackageUninstallResponse(
            ok=False,
            removed=[],
            error=str(exc)
        )