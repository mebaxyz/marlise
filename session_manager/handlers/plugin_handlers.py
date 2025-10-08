"""
Plugin management ZMQ handlers
"""
import logging
from typing import Any, Dict

from .decorators import zmq_handler

logger = logging.getLogger(__name__)


class PluginHandlers:
    """Plugin management ZMQ RPC method handlers"""

    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service

    def register_handlers(self):
        """Register all plugin management handlers using decorator discovery"""
        # Handlers are registered via @zmq_handler decorator by the parent class
        pass

    # Plugin management handlers
    @zmq_handler("get_available_plugins")
    async def handle_get_available_plugins(self, **_kwargs) -> Dict[str, Any]:
        """Get available plugins"""
        try:
            plugins = await self.plugin_manager.get_available_plugins()
            return {"success": True, "plugins": plugins}
        except Exception as e:
            logger.error("Failed to get available plugins: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_plugin")
    async def handle_load_plugin(self, **kwargs) -> Dict[str, Any]:
        """Load plugin"""
        try:
            uri = kwargs.get("uri")
            if not uri:
                return {"success": False, "error": "Missing 'uri' parameter"}

            result = await self.plugin_manager.load_plugin(uri)
            return {"success": True, "instance_id": result["instance_id"], "plugin": result["plugin"]}
        except Exception as e:
            logger.error("Failed to load plugin: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("unload_plugin")
    async def handle_unload_plugin(self, **kwargs) -> Dict[str, Any]:
        """Unload plugin"""
        try:
            instance_id = kwargs.get("instance_id")
            if instance_id is None:
                return {"success": False, "error": "Missing 'instance_id' parameter"}

            await self.plugin_manager.unload_plugin(instance_id)
            return {"success": True}
        except Exception as e:
            logger.error("Failed to unload plugin: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_plugin_info")
    async def handle_get_plugin_info(self, **kwargs) -> Dict[str, Any]:
        """Get plugin info"""
        try:
            instance_id = kwargs.get("instance_id")
            if not instance_id:
                return {"success": False, "error": "Missing 'instance_id' parameter"}

            info = await self.plugin_manager.get_plugin_info(instance_id)
            return {"success": True, "plugin": info["plugin"]}
        except Exception as e:
            logger.error("Failed to get plugin info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_plugins_bulk")
    async def handle_get_plugins_bulk(self, **kwargs) -> Dict[str, Any]:
        """Get bulk plugin information for multiple URIs"""
        try:
            uris = kwargs.get("uris", [])
            if not uris:
                return {"success": False, "error": "Missing 'uris' parameter"}

            if not isinstance(uris, list):
                return {"success": False, "error": "'uris' must be a list"}

            plugins = {}
            for uri in uris:
                try:
                    essentials = await self.plugin_manager.get_plugin_essentials(uri)
                    plugins[uri] = essentials
                except Exception as e:
                    logger.warning("Failed to get essentials for plugin %s: %s", uri, e)
                    plugins[uri] = {"error": str(e)}

            return {"success": True, "plugins": plugins}
        except Exception as e:
            logger.error("Failed to get bulk plugin info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("list_plugins")
    async def handle_list_plugins(self, **_kwargs) -> Dict[str, Any]:
        """List all available plugins (not instances)"""
        try:
            plugins = await self.plugin_manager.get_available_plugins()
            return {"success": True, "plugins": plugins}
        except Exception as e:
            logger.error("Failed to list plugins: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_plugin_info_by_uri")
    async def handle_get_plugin_info_by_uri(self, **kwargs) -> Dict[str, Any]:
        """Get plugin information by URI"""
        try:
            uri = kwargs.get("uri")
            if not uri:
                return {"success": False, "error": "Missing 'uri' parameter"}

            essentials = await self.plugin_manager.get_plugin_essentials(uri)
            return {"success": True, "plugin": essentials}
        except Exception as e:
            logger.error("Failed to get plugin info by URI: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("add_plugin")
    async def handle_add_plugin(self, **kwargs) -> Dict[str, Any]:
        """Add plugin with specific instance ID"""
        try:
            instance_id = kwargs.get("instance_id")
            uri = kwargs.get("uri")
            x = kwargs.get("x", 0.0)
            y = kwargs.get("y", 0.0)

            if not instance_id or not uri:
                return {"success": False, "error": "Missing 'instance_id' or 'uri' parameter"}

            # Load plugin and ensure it gets the specified instance_id
            # This might require modification to plugin_manager
            result = await self.plugin_manager.load_plugin(uri)
            return {"success": True, "instance_id": result["instance_id"], "plugin": result["plugin"]}
        except Exception as e:
            logger.error("Failed to add plugin: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_plugin")
    async def handle_remove_plugin(self, **kwargs) -> Dict[str, Any]:
        """Remove plugin by instance ID"""
        try:
            instance_id = kwargs.get("instance_id")
            if not instance_id:
                return {"success": False, "error": "Missing 'instance_id' parameter"}

            await self.plugin_manager.unload_plugin(instance_id)
            return {"success": True}
        except Exception as e:
            logger.error("Failed to remove plugin: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("list_instances")
    async def handle_list_instances(self, **_kwargs) -> Dict[str, Any]:
        """List plugin instances"""
        try:
            instances = await self.plugin_manager.list_instances()
            return {"success": True, "instances": instances}
        except Exception as e:
            logger.error("Failed to list instances: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_parameter")
    async def handle_set_parameter(self, **kwargs) -> Dict[str, Any]:
        """Set plugin parameter"""
        try:
            instance_id = kwargs.get("instance_id")
            port = kwargs.get("port") or kwargs.get("parameter")  # Support both for compatibility
            value = kwargs.get("value")

            if instance_id is None or port is None or value is None:
                return {"success": False, "error": "Missing required parameters"}

            await self.plugin_manager.set_parameter(instance_id, port, value)
            return {"success": True}
        except Exception as e:
            logger.error("Failed to set parameter: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_parameter")
    async def handle_get_parameter(self, **kwargs) -> Dict[str, Any]:
        """Get plugin parameter"""
        try:
            instance_id = kwargs.get("instance_id")
            port = kwargs.get("port")

            if instance_id is None or port is None:
                return {"success": False, "error": "Missing required parameters"}

            value = await self.plugin_manager.get_parameter(instance_id, port)
            return {"success": True, "value": value}
        except Exception as e:
            logger.error("Failed to get parameter: %s", e)
            return {"success": False, "error": str(e)}