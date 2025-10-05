"""Service for managing session-level audio control operations."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionControlService:
    """Manages session-level audio control operations.

    Handles session initialization, reset, mute/unmute, and state queries.
    """

    def __init__(self, bridge_client, plugin_manager, connection_service, zmq_service=None):
        self.bridge = bridge_client
        self.plugin_manager = plugin_manager
        self.connection_service = connection_service
        self.zmq_service = zmq_service

    async def _clear_audio_state(self):
        """Clear all audio state (plugins and connections)"""
        # Clear connections
        self.connection_service.clear_connections()

        # Clear plugins
        await self.plugin_manager.clear_all()

        logger.debug("Cleared audio state")

    async def reset_session(self, bank_id: Optional[str] = None) -> Dict[str, Any]:
        """Reset entire session state (equivalent to original host reset)"""
        # Clear all audio state first
        await self._clear_audio_state()

        # Reset bridge service state
        try:
            result = await self.bridge.call("modhost_bridge", "reset_session")
            success = result.get("success", False)
        except Exception:
            success = False

        if success:
            # Publish event
            if self.zmq_service:
                await self.zmq_service.publish_event(
                    "session_reset",
                    {"bank_id": bank_id, "timestamp": datetime.now().isoformat()},
                )

            logger.info("Session reset complete")
            return {"status": "ok", "message": "Session reset successfully"}
        else:
            logger.error("Failed to reset mod-host state")
            return {"status": "error", "message": "Failed to reset mod-host state"}

    async def mute_session(self) -> Dict[str, Any]:
        """Mute audio output (disconnect from system output)"""
        try:
            result = await self.bridge.call("modhost_bridge", "mute_session")
            success = result.get("success", False)
        except Exception:
            success = False

        if success:
            # Publish event
            if self.zmq_service:
                await self.zmq_service.publish_event(
                    "session_muted", {"timestamp": datetime.now().isoformat()}
                )

            logger.info("Session muted")
            return {"status": "ok", "muted": True}
        else:
            logger.error("Failed to mute session")
            return {"status": "error", "message": "Failed to mute session"}

    async def unmute_session(self) -> Dict[str, Any]:
        """Unmute audio output (reconnect to system output)"""
        try:
            result = await self.bridge.call("modhost_bridge", "unmute_session")
            success = result.get("success", False)
        except Exception:
            success = False

        if success:
            # Publish event
            if self.zmq_service:
                await self.zmq_service.publish_event(
                    "session_unmuted", {"timestamp": datetime.now().isoformat()}
                )

            logger.info("Session unmuted")
            return {"status": "ok", "muted": False}
        else:
            logger.error("Failed to unmute session")
            return {"status": "error", "message": "Failed to unmute session"}

    async def get_session_state(self) -> Dict[str, Any]:
        """Get comprehensive session state information"""
        # Get system state from bridge
        result = await self.bridge.call("modhost_bridge", "get_session_state")
        system_state = result if result.get("success", False) else {}

        # Get session manager status
        session_status = {
            "active_connections": len(self.connection_service.connections),
            "loaded_plugins": len(self.plugin_manager.instances),
        }

        # Combine state information
        state = {
            "session": session_status,
            "system": system_state,
            "timestamp": datetime.now().isoformat(),
        }

        return state

    async def initialize_session(self) -> Dict[str, Any]:
        """Initialize session (equivalent to original init_host)"""
        try:
            # Reset any existing state
            await self._clear_audio_state()

            # Initialize bridge service
            try:
                result = await self.bridge.call("modhost_bridge", "initialize_session")
                success = result.get("success", False)
            except Exception:
                success = False

            if success:
                # Publish event
                if self.zmq_service:
                    await self.zmq_service.publish_event(
                        "session_initialized",
                        {"timestamp": datetime.now().isoformat()},
                    )

                logger.info("Session initialized successfully")
                return {"status": "ok", "message": "Session initialized"}
            else:
                logger.error("Failed to initialize session")
                return {
                    "status": "error",
                    "message": "Failed to initialize session",
                }

        except Exception as e:
            logger.error("Error during session initialization: %s", e)
            return {"status": "error", "message": f"Initialization error: {e}"}