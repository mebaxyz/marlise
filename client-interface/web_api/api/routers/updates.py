"""
System Updates and Package Management API endpoints
"""
from fastapi import APIRouter, File, UploadFile

from ..models import (
    PackageUninstallRequest, PackageUninstallResponse
)

from fastapi import Request
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["updates"])


@router.post("/update/begin")
async def begin_update(request: Request):
    """Start system update/restore process.

    TODO: trigger the system update flow through the session manager and return immediate status.
    """
    # Call session manager to begin update
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "begin_update", timeout=5.0)
        resp = await asyncio.wait_for(fut, timeout=10.0)  # Longer timeout for update process
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("begin_update timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling begin_update: %s", exc)
        return {"ok": False}


@router.post("/update/download")
async def upload_system_image(request: Request, file: UploadFile = File(...)):
    """Upload system image file for firmware update.

    TODO: validate image, stage to temp location and pass to update process via session manager.
    """
    # Process uploaded system image
    zmq_client = getattr(request.app.state, 'zmq_client', None) if request is not None else None
    if zmq_client is None:
        return {
            "ok": False,
            "result": False
        }

    try:
        # Read file content
        file_data = await file.read()
        filename = file.filename

        fut = zmq_client.call("session_manager", "upload_system_image", file_data=file_data, filename=filename, timeout=5.0)
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
async def upload_controlchain_firmware(request: Request, file: UploadFile = File(...)):
    """Upload firmware for Control Chain hardware devices.

    TODO: stage firmware and instruct control chain updater via session manager.
    """
    # Process uploaded Control Chain firmware
    zmq_client = getattr(request.app.state, 'zmq_client', None) if request is not None else None
    if zmq_client is None:
        return {
            "ok": False,
            "result": False
        }

    try:
        # Read file content
        file_data = await file.read()
        filename = file.filename

        fut = zmq_client.call("session_manager", "upload_controlchain_firmware", file_data=file_data, filename=filename, timeout=5.0)
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
async def cancel_controlchain_update(request: Request):
    """Cancel ongoing Control Chain firmware update.

    TODO: notify session manager to cancel update process safely.
    """
    # Cancel Control Chain update
    zmq_client = getattr(request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return {"ok": False}

    try:
        fut = zmq_client.call("session_manager", "cancel_controlchain_update", timeout=5.0)
        resp = await asyncio.wait_for(fut, timeout=10.0)
        return {"ok": isinstance(resp, dict) and resp.get("success", False)}
    except asyncio.TimeoutError:
        logger.warning("cancel_controlchain_update timed out")
        return {"ok": False}
    except Exception as exc:
        logger.exception("Error calling cancel_controlchain_update: %s", exc)
        return {"ok": False}


@router.post("/package/uninstall")
async def uninstall_package(request: PackageUninstallRequest, http_request: Request):
    """Uninstall plugin packages.

    TODO: forward uninstall list to session manager, return removed bundles and errors.
    """
    # Call session manager to uninstall packages
    zmq_client = getattr(http_request.app.state, 'zmq_client', None)
    if zmq_client is None:
        return PackageUninstallResponse(
            ok=False,
            removed=[],
            error="ZMQ client not available"
        )

    try:
        fut = zmq_client.call("session_manager", "uninstall_package", packages=request.bundles, timeout=5.0)
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