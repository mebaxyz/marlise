"""
Moved Client Interface main app (copied from previous location).
"""

# ...existing code...

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .routers import auth as auth_router
from .routers import banks as banks_router
from .routers import favorites as favorites_router
from .routers import files as files_router
from .routers import health as health_router
from .routers import jack as jack_router
from .routers import misc as misc_router
from .routers import pedalboards as pedalboards_router
from .routers import plugins as plugins_router
from .routers import recording as recording_router
from .routers import snapshots as snapshots_router
from .routers import system as system_router
from .routers import updates as updates_router
from .zmq_client import ZMQClient

# Configuration
SERVICE_NAME = "client_interface"
SERVICE_PORT = int(os.getenv("CLIENT_INTERFACE_PORT", "8080"))
HTML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../static"))

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket
        logger.info("WebSocket connected: %d active connections", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from user connections if present
        for user_id, user_ws in list(self.user_connections.items()):
            if user_ws == websocket:
                del self.user_connections[user_id]
                break
        logger.info("WebSocket disconnected: %d active connections", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Failed to send to WebSocket: %s", e)
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception as e:
                logger.warning("Failed to send to user %s: %s", user_id, e)
                await self.disconnect(self.user_connections[user_id])


# Request/Response Models
class PluginRequest(BaseModel):
    uri: str
    x: float = 0.0
    y: float = 0.0


class ParameterUpdate(BaseModel):
    instance_id: str
    parameter: str
    value: float


class PedalboardRequest(BaseModel):
    bundlepath: str


class ConfigSettingRequest(BaseModel):
    key: str
    value: Any


# Config API Models


# Global instances
connection_manager = ConnectionManager()
zmq_client: Optional[ZMQClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global zmq_client

    # Startup
    logger.info("Starting %s service on port %d", SERVICE_NAME, SERVICE_PORT)

    # Initialize ZMQ client
    zmq_client = ZMQClient(SERVICE_NAME)
    await zmq_client.start()

    # Export the ZMQ client on the application state to avoid circular imports
    # from router modules. Routers can access it via `request.app.state.zmq_client`.
    try:
        app.state.zmq_client = zmq_client
    except Exception:
        # `app` may not be fully initialized in some contexts; routers should
        # use request.app.state for runtime access.
        pass

    logger.info("ZMQ client started")
    logger.info("%s service started successfully", SERVICE_NAME)

    try:
        yield
    finally:
        # Cleanup
        logger.info("Shutting down %s service", SERVICE_NAME)

        # Stop ZMQ client
        if zmq_client:
            await zmq_client.stop()

        logger.info("%s service stopped", SERVICE_NAME)


# Create FastAPI application
app = FastAPI(
    title="MOD UI Client Interface",
    description="Web client interface for MOD UI audio processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Include all routers organized by responsibility
app.include_router(health_router.router)
app.include_router(plugins_router.router)
app.include_router(pedalboards_router.router)
app.include_router(snapshots_router.router)
app.include_router(banks_router.router)
app.include_router(favorites_router.router)
app.include_router(recording_router.router)
app.include_router(system_router.router)
app.include_router(jack_router.router)
app.include_router(files_router.router)
app.include_router(auth_router.router)
app.include_router(updates_router.router)
app.include_router(misc_router.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
if os.path.exists(HTML_DIR):
    app.mount("/static", StaticFiles(directory=HTML_DIR), name="static")
    logger.info("Serving static files from %s", HTML_DIR)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": SERVICE_NAME,
        "status": "healthy",
        "details": {
            "active_connections": len(connection_manager.active_connections),
            "zmq_client_connected": (zmq_client.is_connected() if zmq_client else False),
        },
    }


# (rest of API unchanged)`
