"""Utility helpers for session-manager core."""
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict


def serialize_pedalboard(pedalboard) -> Dict[str, Any]:
    """Return a JSON-serializable dict for a Pedalboard (datetimes -> isoformat)."""
    pb = asdict(pedalboard)

    if isinstance(pedalboard.created_at, datetime):
        pb["created_at"] = pedalboard.created_at.isoformat()
    if isinstance(pedalboard.modified_at, datetime):
        pb["modified_at"] = pedalboard.modified_at.isoformat()

    # ensure connections are basic dicts
    if "connections" in pb:
        serialized_conns = []
        for c in pb["connections"]:
            if isinstance(c, dict):
                serialized_conns.append(c)
            else:
                try:
                    serialized_conns.append(asdict(c))
                except Exception:
                    serialized_conns.append({})
        pb["connections"] = serialized_conns

    return pb
