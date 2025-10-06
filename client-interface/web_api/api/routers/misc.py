"""
Miscellaneous API endpoints
"""
from fastapi import APIRouter, Form
from fastapi.responses import Response

from ..models import UserIdSaveRequest, StatusResponse

router = APIRouter(tags=["misc"])


@router.get("/ping")
async def ping():
    """NOT IMPLEMENTED: Simple ping endpoint.

    TODO: keep lightweight for quick probes or forward to /system/ping for device checks.
    """
    # This could be different from /system/ping - simpler version
    return {"ok": True, "message": "pong"}


@router.get("/hello")  
async def hello():
    """NOT IMPLEMENTED: Hello endpoint (placeholder).

    TODO: remove or replace with actual service metadata endpoint.
    """
    return {"message": "Hello from MOD UI API"}


@router.post("/save_user_id")
async def save_user_id(
    name: str = Form(...),
    email: str = Form(...)
):
    """NOT IMPLEMENTED: Store user identity information for sharing features.

    TODO: persist user identity via session manager/preferences store for sharing workflows.
    """
    # Call session manager to save user ID
    return {"ok": False}


# Static resource handlers (these might be handled by static file serving instead)
@router.get("/resources/{path:path}")
async def serve_resources(path: str):
    """NOT IMPLEMENTED: Serve static UI resources (images, fonts, CSS, JS files).

    TODO: prefer mounting StaticFiles and avoid implementing ad-hoc resource serving here.
    """
    # This would typically be handled by FastAPI's StaticFiles
    return Response(content=b"", media_type="application/octet-stream")


@router.get("/load_template/{name}.html")
async def load_template(name: str):
    """NOT IMPLEMENTED: Serve HTML templates for dynamic UI components.

    TODO: read from HTML include directory or static bundle and return template content.
    """
    # Load and return template file
    return Response(content="", media_type="text/html")


@router.get("/js/templates.js")
async def get_compiled_templates():
    """NOT IMPLEMENTED: Serve compiled JavaScript template definitions.

    TODO: build or load precompiled templates.js and return its content.
    """
    # Return compiled templates
    return Response(content="", media_type="application/javascript")