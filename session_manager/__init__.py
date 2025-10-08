"""Package shim for session manager modules.

This package provides a stable Python import path `session_manager` used by
other modules and tests. It intentionally lives alongside the legacy
filesystem directory `session-manager` to avoid renaming files used by
deployment scripts.
"""

__all__ = ["zmq_handlers"]
