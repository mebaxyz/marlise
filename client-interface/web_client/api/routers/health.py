from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def api_health():
    """Lightweight API health endpoint for the web client dev server to probe.

    This endpoint does not call session_manager; it simply reports that the
    adapter process is alive and able to service simple requests.
    """
    return {"service": "client_interface", "status": "ok"}
