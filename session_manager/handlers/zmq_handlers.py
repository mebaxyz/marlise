"""
Main ZMQ handlers module - imports and registers all handler modules

This file maintains backward compatibility while delegating to the new modular structure.
"""

import logging
from typing import Any, Dict, Callable, Optional

from .decorators import zmq_handler
from .plugin_handlers import PluginHandlers
from .pedalboard_handlers import PedalboardHandlers
from .jack_handlers import JackHandlers
from .system_handlers import SystemHandlers

logger = logging.getLogger(__name__)


class ZMQHandlers:
    """
    ZeroMQ RPC method handlers for audio processing service.

    This class now delegates to modular handler classes for better maintainability:
    - PluginHandlers: Plugin management operations
    - PedalboardHandlers: Pedalboard operations
    - JackHandlers: JACK audio system operations
    - SystemHandlers: System control, snapshots, banks, etc.
    """

    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service

        # Initialize handler modules
        self.plugin_handlers = PluginHandlers(
            bridge_client, plugin_manager, session_manager, zmq_service
        )
        self.pedalboard_handlers = PedalboardHandlers(
            bridge_client, plugin_manager, session_manager, zmq_service
        )
        self.jack_handlers = JackHandlers(
            bridge_client, plugin_manager, session_manager, zmq_service
        )
        self.system_handlers = SystemHandlers(
            bridge_client, plugin_manager, session_manager, zmq_service
        )

        # Register all handlers
        self._register_all_handlers()

    def _register_all_handlers(self):
        """Register all handlers using decorator discovery"""
        logger.info("Registering ZMQ handlers via decorator discovery...")

        # Use the decorator-based registration
        self.register_service_methods()

        logger.info("All ZMQ handlers registered successfully")

    def register_service_methods(self):
        """
        Register all methods marked with @zmq_handler decorator.
        
        This method discovers all methods in this class and its handler modules
        that have been marked with the @zmq_handler decorator and registers them
        with the ZMQ service.
        """
        logger.info("Registering service methods with @zmq_handler decorator...")

        # Register methods from this class
        self._register_marked_methods(self)

        # Register methods from handler modules
        self._register_marked_methods(self.plugin_handlers)
        self._register_marked_methods(self.pedalboard_handlers)
        self._register_marked_methods(self.jack_handlers)
        self._register_marked_methods(self.system_handlers)

        logger.info("Service methods registration complete")

    def _register_marked_methods(self, obj):
        """Register all methods marked with @zmq_handler in the given object"""
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue

            attr = getattr(obj, attr_name)
            if callable(attr) and hasattr(attr, '_zmq_handler_marked'):
                method_name = getattr(attr, '_zmq_handler_name')
                self.zmq_service.register_handler(method_name, attr)
                logger.debug("Registered handler: %s -> %s.%s", method_name, obj.__class__.__name__, attr_name)

    # Legacy methods for backward compatibility (if needed)
    # These delegate to the appropriate handler modules

    async def handle_get_available_plugins(self, **kwargs) -> Dict[str, Any]:
        """Legacy method - delegates to PluginHandlers"""
        return await self.plugin_handlers.handle_get_available_plugins(**kwargs)

    async def handle_load_plugin(self, **kwargs) -> Dict[str, Any]:
        """Legacy method - delegates to PluginHandlers"""
        return await self.plugin_handlers.handle_load_plugin(**kwargs)

    async def handle_unload_plugin(self, **kwargs) -> Dict[str, Any]:
        """Legacy method - delegates to PluginHandlers"""
        return await self.plugin_handlers.handle_unload_plugin(**kwargs)

    async def handle_reset_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Legacy method - delegates to PedalboardHandlers"""
        return await self.pedalboard_handlers.handle_reset_pedalboard(**kwargs)
