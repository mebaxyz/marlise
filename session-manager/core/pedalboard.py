"""
Pedalboard dataclass for session-manager
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import Connection


@dataclass
class Pedalboard:
    """Represents a complete pedalboard configuration with helpers.

    This remains a dataclass so `asdict()` works for serialization helpers.
    """

    id: str
    name: str
    description: str
    plugins: List[Dict[str, Any]]
    connections: List[Connection]
    created_at: datetime
    modified_at: datetime
    metadata: Dict[str, Any]
    # System I/O configuration - always present elements
    system_inputs: Optional[List[str]] = None  # e.g., ["system:capture_1", "system:capture_2"]
    system_outputs: Optional[List[str]] = None  # e.g., ["system:playbook_1", "system:playback_2"]

    def add_plugin(self, plugin: Dict[str, Any]) -> str:
        """Add a plugin config to the pedalboard. Returns the new instance_id if present."""
        self.plugins.append(plugin)
        self.modified_at = datetime.now()
        return plugin.get("instance_id", "")

    def remove_plugin(self, instance_id: str) -> bool:
        """Remove a plugin by instance_id. Returns True if removed."""
        before = len(self.plugins)
        self.plugins = [p for p in self.plugins if p.get("instance_id") != instance_id]
        removed = len(self.plugins) < before
        if removed:
            self.modified_at = datetime.now()
        return removed

    def find_plugin(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Find and return a plugin dict by instance_id."""
        for p in self.plugins:
            if p.get("instance_id") == instance_id:
                return p
        return None

    def add_connection(self, connection: Connection) -> str:
        """Add a Connection object to the pedalboard and return its id."""
        self.connections.append(connection)
        self.modified_at = datetime.now()
        return connection.connection_id

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection by id. Returns True if removed."""
        before = len(self.connections)
        self.connections = [c for c in self.connections if c.connection_id != connection_id]
        removed = len(self.connections) < before
        if removed:
            self.modified_at = datetime.now()
        return removed

    def set_system_inputs(self, inputs: List[str]) -> None:
        """Set system input ports for this pedalboard."""
        self.system_inputs = inputs.copy() if inputs else []
        self.modified_at = datetime.now()

    def set_system_outputs(self, outputs: List[str]) -> None:
        """Set system output ports for this pedalboard."""
        self.system_outputs = outputs.copy() if outputs else []
        self.modified_at = datetime.now()

    def get_system_inputs(self) -> List[str]:
        """Get system input ports, defaulting to standard stereo inputs."""
        return self.system_inputs if self.system_inputs is not None else ["system:capture_1", "system:capture_2"]

    def get_system_outputs(self) -> List[str]:
        """Get system output ports, defaulting to standard stereo outputs."""
        return self.system_outputs if self.system_outputs is not None else ["system:playback_1", "system:playback_2"]

    def to_dict(self) -> Dict[str, Any]:
        """Convenience serialization (delegates to dataclass asdict)."""
        data = asdict(self)
        # datetimes will be serialized by utils.serialize_pedalboard
        return data

