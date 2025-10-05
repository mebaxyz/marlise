"""
Moved Client Interface main app (copied from previous location).
"""

# ...existing code...

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
import zmq
import zmq.asyncio
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .zmq_client import ZMQClient
from .routers import health as health_router

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
        logger.info(
            f"WebSocket connected: {len(self.active_connections)} active connections"
        )

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from user connections if present
        for user_id, user_ws in list(self.user_connections.items()):
            if user_ws == websocket:
                del self.user_connections[user_id]
                break
        logger.info(
            f"WebSocket disconnected: {len(self.active_connections)} active connections"
        )

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
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
                logger.warning(f"Failed to send to user {user_id}: {e}")
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
    logger.info(f"Starting {SERVICE_NAME} service on port {SERVICE_PORT}")

    # Initialize ZMQ client
    zmq_client = ZMQClient(SERVICE_NAME)
    await zmq_client.start()

    logger.info("ZMQ client started")
    logger.info(f"{SERVICE_NAME} service started successfully")

    try:
        yield
    finally:
        # Cleanup
        logger.info(f"Shutting down {SERVICE_NAME} service")

        # Stop ZMQ client
        if zmq_client:
            await zmq_client.stop()

        logger.info(f"{SERVICE_NAME} service stopped")


# Create FastAPI application
app = FastAPI(
    title="MOD UI Client Interface",
    description="Web client interface for MOD UI audio processing",
    version="1.0.0",
    lifespan=lifespan,
)

# include small routers
app.include_router(health_router.router)

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
    logger.info(f"Serving static files from {HTML_DIR}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": SERVICE_NAME,
        "status": "healthy",
        "details": {
            "active_connections": len(connection_manager.active_connections),
            "zmq_client_connected": (
                zmq_client.is_connected() if zmq_client else False
            ),
        },
    }


# (rest of API unchanged)`
