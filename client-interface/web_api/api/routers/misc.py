"""
Miscellaneous API endpoints
"""
from fastapi import APIRouter, Form
from fastapi.responses import Response

from ..models import UserIdSaveRequest, StatusResponse

router = APIRouter(tags=["misc"])


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    # This could be different from /system/ping - simpler version
    return {"ok": True, "message": "pong"}


@router.get("/hello")  
async def hello():
    """Hello endpoint"""
    return {"message": "Hello from MOD UI API"}


@router.post("/save_user_id")
async def save_user_id(
    name: str = Form(...),
    email: str = Form(...)
):
    """Store user identity information for sharing features"""
    # Call session manager to save user ID
    return {"ok": False}


# Static resource handlers (these might be handled by static file serving instead)
@router.get("/resources/{path:path}")
async def serve_resources(path: str):
    """Serve static UI resources (images, fonts, CSS, JS files)"""
    # This would typically be handled by FastAPI's StaticFiles
    return Response(content=b"", media_type="application/octet-stream")


@router.get("/load_template/{name}.html")
async def load_template(name: str):
    """Serve HTML templates for dynamic UI components"""
    # Load and return template file
    return Response(content="", media_type="text/html")


@router.get("/js/templates.js")
async def get_compiled_templates():
    """Serve compiled JavaScript template definitions"""
    # Return compiled templates
    return Response(content="", media_type="application/javascript")