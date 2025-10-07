"""
MOD UI - Audio Processing Service - Session Manager

Manages pedalboard sessions, snapshots, and state persistence.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Localized pylint - this module intentionally has several broad except handlers
# pylint: disable=broad-except


from ..models.pedalboard_service import PedalboardService
from ..services.connection_service import ConnectionService
from .session_control_service import SessionControlService


class SessionManager:
    """Main coordinator for pedalboard sessions and audio state management.

    Delegates to specialized services:
    - PedalboardService: handles pedalboard lifecycle (create/load/save/snapshots)
    - ConnectionService: handles audio connections between plugins
    - SessionControlService: handles session-level audio control operations
    """

    def __init__(self, plugin_manager, bridge_client, zmq_service=None):
        self.plugin_manager = plugin_manager
        self.bridge = bridge_client
        self.zmq_service = zmq_service

        # Initialize services with bridge client directly
        self.pedalboard_service = PedalboardService(plugin_manager, bridge_client, zmq_service)
        self.connection_service = ConnectionService(bridge_client, self.pedalboard_service, plugin_manager, zmq_service)
        self.session_control = SessionControlService(bridge_client, plugin_manager, self.connection_service, zmq_service)

        # Simplified locking for session-level operations only
        self._lock = asyncio.Lock()

    async def create_pedalboard(
        self, name: str, description: str = ""
    ) -> Dict[str, Any]:
        """Create a new empty pedalboard"""
        async with self._lock:
            # Clear current audio state
            await self.session_control._clear_audio_state()

            # Delegate to pedalboard service - it handles all state management
            result = await self.pedalboard_service.create_pedalboard(name, description)

            # Reset connections
            self.connection_service.clear_connections()

            return result

    async def load_pedalboard(self, pedalboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a pedalboard from configuration data"""
        async with self._lock:
            # Clear current state
            await self.session_control._clear_audio_state()

            # Delegate to pedalboard service - it handles all state management
            result = await self.pedalboard_service.load_pedalboard(pedalboard_data)

            # Sync connections from pedalboard service
            self.connection_service.connections = self.pedalboard_service.connections

            return result

    async def save_pedalboard(self) -> Dict[str, Any]:
        """Save current pedalboard state (persist to disk)."""
        # Sync current connection state to pedalboard service
        self.pedalboard_service.connections = self.connection_service.connections

        # Delegate to pedalboard service - it validates and saves
        return await self.pedalboard_service.save_pedalboard()

    async def get_current_pedalboard(self, *, persist: bool = True) -> Dict[str, Any]:
        """Get current pedalboard state.

        persist=False can be used by offline/demo tools to avoid disk writes.
        """
        return await self.pedalboard_service.get_current_pedalboard(persist=persist)

    async def create_connection(
        self, source_plugin: str, source_port: str, target_plugin: str, target_port: str
    ) -> Dict[str, Any]:
        """Create a connection between plugins"""
        # Delegate to connection service - it handles validation and creation
        return await self.connection_service.create_connection(
            source_plugin, source_port, target_plugin, target_port
        )

    async def remove_connection(self, connection_id: str) -> Dict[str, Any]:
        """Remove a connection"""
        # Delegate to connection service
        return await self.connection_service.remove_connection(connection_id)

    async def create_snapshot(self, name: str) -> Dict[str, Any]:
        """Create a snapshot of current state"""
        # Delegate to pedalboard service
        return await self.pedalboard_service.create_snapshot(name)

    async def apply_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a snapshot to current state"""
        # Delegate to pedalboard service
        return await self.pedalboard_service.apply_snapshot(snapshot)

    # Session Control Methods - delegate to session control service
    async def reset_session(self, bank_id: Optional[str] = None) -> Dict[str, Any]:
        """Reset entire session state"""
        async with self._lock:
            return await self.session_control.reset_session(bank_id)

    async def mute_session(self) -> Dict[str, Any]:
        """Mute audio output"""
        return await self.session_control.mute_session()

    async def unmute_session(self) -> Dict[str, Any]:
        """Unmute audio output"""
        return await self.session_control.unmute_session()

    async def get_session_state(self) -> Dict[str, Any]:
        """Get comprehensive session state information"""
        return await self.session_control.get_session_state()

    async def initialize_session(self) -> Dict[str, Any]:
        """Initialize session"""
        async with self._lock:
            return await self.session_control.initialize_session()

    def get_status(self) -> Dict[str, Any]:
        """Get session manager status"""
        current_pb = self.pedalboard_service.current_pedalboard
        return {
            "current_pedalboard": current_pb.name if current_pb else None,
            "pedalboard_id": current_pb.id if current_pb else None,
            "active_connections": len(self.connection_service.connections),
            "loaded_plugins": len(self.plugin_manager.instances),
        }
