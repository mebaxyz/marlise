"""
Connection dataclass for session-manager
"""
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class Connection:
    """Represents an audio connection between plugins"""

    source_plugin: str
    source_port: str
    target_plugin: str
    target_port: str
    connection_id: Optional[str] = None

    def __post_init__(self):
        if not self.connection_id:
            self.connection_id = str(uuid.uuid4())
