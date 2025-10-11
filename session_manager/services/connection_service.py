"""Service for managing audio connections between plugins."""
import logging
from typing import Any, Dict
from dataclasses import asdict

from ..models.connection import Connection
from ..managers.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class ConnectionService:
    """Manages audio connections between plugins.

    Handles creation, removal, and listing of connections.
    Uses audio_system for bridge calls and pedalboard_service for persistence.
    """

    def __init__(self, bridge_client, pedalboard_service, plugin_manager, zmq_service=None):
        self.bridge = bridge_client
        self.pedalboard_service = pedalboard_service
        self.plugin_manager = plugin_manager
        self.zmq_service = zmq_service
        self.connections = ConnectionManager([])

    async def create_connection(
        self, source_plugin: str, source_port: str, target_plugin: str, target_port: str
    ) -> Dict[str, Any]:
        """Create a connection between plugins"""
        # Validate plugins exist
        if source_plugin not in self.plugin_manager.instances:
            raise ValueError(f"Source plugin not found: {source_plugin}")
        if target_plugin not in self.plugin_manager.instances:
            raise ValueError(f"Target plugin not found: {target_plugin}")

        # Create connection object
        connection = Connection(
            source_plugin=source_plugin,
            source_port=source_port,
            target_plugin=target_plugin,
            target_port=target_port,
        )

        # Create connection in bridge service
        try:
            result = await self.bridge.call("modhost_bridge", "create_connection", source_plugin=source_plugin, source_port=source_port, target_plugin=target_plugin, target_port=target_port)
            if not result.get("success", False):
                raise RuntimeError(result.get("error", "Failed to create connection"))
        except Exception as e:
            raise RuntimeError(str(e))

        # Store connection
        self.connections.append(connection)

        # Update pedalboard if loaded
        if self.pedalboard_service.current_pedalboard:
            self.pedalboard_service.add_connection(connection)

        # Publish event
        if self.zmq_service:
            await self.zmq_service.publish_event(
                "connection_created",
                {
                    "connection_id": connection.connection_id,
                    "source": f"{source_plugin}:{source_port}",
                    "target": f"{target_plugin}:{target_port}",
                },
            )

        logger.info(
            "Created connection: %s:%s -> %s:%s",
            source_plugin,
            source_port,
            target_plugin,
            target_port,
        )

        return {
            "connection_id": connection.connection_id,
            "connection": asdict(connection),
        }

    async def remove_connection(self, connection_id: str) -> Dict[str, Any]:
        """Remove a connection"""
        # Find connection
        connection = self.connections.find(connection_id)
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        # Disconnect via bridge
        try:
            result = await self.bridge.call("modhost_bridge", "remove_connection", connection_id=connection_id)
            if not result.get("success", False):
                logger.warning("Failed to disconnect in mod-host: %s (%s)", connection_id, result.get("error", "Unknown error"))
        except Exception as e:
            logger.warning("Failed to disconnect in mod-host: %s (%s)", connection_id, e)

        # Remove from connections
        self.connections.remove(connection)

        # Update pedalboard if loaded
        if self.pedalboard_service.current_pedalboard:
            self.pedalboard_service.remove_connection(connection_id)

        # Publish event
        if self.zmq_service:
            await self.zmq_service.publish_event(
                "connection_removed", {"connection_id": connection_id}
            )

        logger.info("Removed connection %s", connection_id)

        return {"status": "ok", "connection_id": connection_id}

    def get_connections(self) -> list:
        """Get all current connections"""
        return self.connections.all()

    def clear_connections(self):
        """Clear all connections"""
        self.connections = ConnectionManager([])