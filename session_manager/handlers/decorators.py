"""
ZMQ handler decorators
"""
from typing import Callable, Union


def zmq_handler(name: Union[str, None]) -> Callable:
    """Decorator to mark a method as an RPC handler.

    Usage:
        @zmq_handler('custom_name')
        async def my_handler(self, **kwargs):
            ...

    The decorator sets attributes on the function so the registrar can
    discover and register only explicitly-marked handlers. It does NOT
    alter the method behavior; handlers should return their own
    "not implemented" response if appropriate (keeps behavior explicit).
    """

    if not name or not isinstance(name, str):
        raise TypeError("zmq_handler requires a non-empty name")

    def decorator(fn: Callable) -> Callable:
        setattr(fn, "_zmq_handler_name", name)
        setattr(fn, "_zmq_handler_marked", True)
        return fn

    return decorator
