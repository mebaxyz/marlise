"""
ZMQ handler decorators
"""
from typing import Callable


def zmq_handler(name: str) -> Callable:
    """Decorator to explicitly mark a method as an RPC handler.

    Usage:
        @zmq_handler('custom_name')
        async def my_handler(self, **kwargs):
            ...

    The decorator requires a non-empty name. The registrar will use the
    provided name exactly as the external RPC method name. The decorator
    sets attributes on the function so the registrar can discover and
    register only explicitly-marked handlers.
    """

    if not name:
        raise TypeError("zmq_handler requires a non-empty name")

    def decorator(fn: Callable) -> Callable:
        setattr(fn, "_zmq_handler_name", name)
        setattr(fn, "_zmq_handler_marked", True)
        return fn

    return decorator
