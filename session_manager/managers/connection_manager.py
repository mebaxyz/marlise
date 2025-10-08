"""Simple manager for connections to decouple list handling from SessionManager."""
from typing import List, Optional

from ..models.connection import Connection


class ConnectionManager:
    """Keep and manage Connection objects."""

    def __init__(self, initial: Optional[List[Connection]] = None):
        self._connections: List[Connection] = list(initial or [])

    def add(self, connection: Connection) -> None:
        self._connections.append(connection)

    # list-like alias
    def append(self, connection: Connection) -> None:
        self.add(connection)

    def remove(self, connection_or_id) -> bool:
        """Remove by connection_id or by Connection object.

        If passed a Connection object, it will be removed. Returns True if removed.
        """
        # accept either Connection or connection_id
        target_id = None
        if hasattr(connection_or_id, "connection_id"):
            target_id = connection_or_id.connection_id
        else:
            target_id = connection_or_id

        before = len(self._connections)
        self._connections = [c for c in self._connections if c.connection_id != target_id]
        return len(self._connections) < before

    def find(self, connection_id: str) -> Optional[Connection]:
        for c in self._connections:
            if c.connection_id == connection_id:
                return c
        return None

    def all(self) -> List[Connection]:
        return list(self._connections)

    def __iter__(self):
        return iter(self._connections)

    def __len__(self):
        return len(self._connections)
