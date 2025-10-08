import logging
from typing import Any, Dict, Callable, Optional

logger = logging.getLogger(__name__)


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


class ZMQHandlers:
    """ZeroMQ RPC method handlers for audio processing service"""
    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service

    def register_service_methods(self):
        """Register all ZeroMQ RPC methods by discovering methods named
        ``handle_<method_name>`` on this instance. Optionally a handler can
        be decorated with ``@zmq_handler('explicit_name')`` to override the
        exposed method name.
        """
        registered = 0
        # Register only explicitly-decorated handlers. This keeps the
        # registration table explicit and avoids accidental exposure of
        # methods that weren't intended to be RPC handlers.
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if not callable(method):
                continue
            if not getattr(method, "_zmq_handler_marked", False):
                continue
            zmq_name = getattr(method, "_zmq_handler_name", None)
            if not zmq_name:
                if attr_name.startswith("handle_"):
                    zmq_name = attr_name[len("handle_"):]
                else:
                    zmq_name = attr_name
            self.zmq_service.register_handler(zmq_name, method)
            registered += 1

        logger.info("ZeroMQ methods registered: %s", registered)

    # --- Internal helpers -------------------------------------------------
    async def _call_bridge(self, method: str, **params):
        """Call the modhost_bridge via bridge_client and return raw result.

        Returns None on exception (caller should handle missing result).
        """
        try:
            result = await self.bridge_client.call("modhost_bridge", method, **params)

            # Normalize legacy bridge responses: the C++ bridge often returns
            # plain JSON objects (e.g. {"sample_rate": 0.0} or {"plugins": {...}})
            # without a top-level "success" boolean. The session-manager
            # handlers expect a {"success": True, ...} shape. Wrap non-error
            # dicts with success=True so callers behave consistently.
            if isinstance(result, dict):
                # If the bridge returned an explicit error, preserve it
                if result.get("error"):
                    return {"success": False, "error": result.get("error")}

                # If there's no explicit success flag, treat as success and
                # merge returned fields under a success envelope.
                if "success" not in result:
                    normalized = {"success": True}
                    normalized.update(result)
                    return normalized

                # Already in canonical form
                return result

            # Non-dict results (e.g. primitives) -> wrap into success/result
            return {"success": True, "result": result}
        except Exception as e:
            # Return error payload so callers can surface original error messages
            err = str(e)
            logger.error("Bridge call '%s' failed: %s", method, err)
            return {"success": False, "error": err}

    def _success_or_error(self, result, ok_map=None, *, err_msg: str = "Operation failed"):
        """Normalize bridge result into a standard success/error dict.

        ok_map: mapping of output key -> result key to include when success is True.
        """
        if result and result.get("success", False):
            resp = {"success": True}
            if ok_map:
                for out_key, res_key in ok_map.items():
                    resp[out_key] = result.get(res_key)
            return resp
        # If the bridge provided an error message, surface it directly
        if result and result.get("error"):
            return {"success": False, "error": result.get("error")}
        return {"success": False, "error": err_msg}


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

    # Pedalboard management handlers
    @zmq_handler("create_pedalboard")
    async def handle_create_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Create pedalboard"""
        try:
            name = kwargs.get("name", "Untitled")
            pedalboard = await self.session_manager.create_pedalboard(name)
            return {"success": True, "pedalboard": pedalboard}
        except Exception as e:
            logger.error("Failed to create pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_pedalboard")
    async def handle_load_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Load pedalboard"""
        try:
            data = kwargs.get("data")
            if not data:
                return {"success": False, "error": "Missing 'data' parameter"}

            await self.session_manager.load_pedalboard(data)
            return {"success": True}
        except Exception as e:
            logger.error("Failed to load pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("save_pedalboard")
    async def handle_save_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Save pedalboard"""
        try:
            filename = kwargs.get("filename")
            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}

            await self.session_manager.save_pedalboard(filename)
            return {"success": True}
        except Exception as e:
            logger.error("Failed to save pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_current_pedalboard")
    async def handle_get_current_pedalboard(self, **_kwargs) -> Dict[str, Any]:
        """Get current pedalboard"""
        try:
            pedalboard = await self.session_manager.get_current_pedalboard()
            return {"success": True, "pedalboard": pedalboard}
        except Exception as e:
            logger.error("Failed to get current pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("setup_system_io")
    async def handle_setup_system_io(self, **_kwargs) -> Dict[str, Any]:
        """Setup system I/O connections for current pedalboard"""
        try:
            result = await self.session_manager.pedalboard_service.setup_system_io_connections()
            return {"success": True, "system_io": result}
        except Exception as e:
            logger.error("Failed to setup system I/O: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_pedalboard_list")
    async def handle_get_pedalboard_list(self, **_kwargs) -> Dict[str, Any]:
        """Get list of all available pedalboards"""
        try:
            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Get pedalboard list not implemented"}
        except Exception as e:
            logger.error("Failed to get pedalboard list: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("save_current_pedalboard")
    async def handle_save_current_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Save current pedalboard state"""
        try:
            title = kwargs.get("title")
            as_new = kwargs.get("as_new", 0)

            if not title:
                return {"success": False, "error": "Missing 'title' parameter"}

            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Save current pedalboard not implemented"}
        except Exception as e:
            logger.error("Failed to save current pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("pack_pedalboard_bundle")
    async def handle_pack_pedalboard_bundle(self, **kwargs) -> Dict[str, Any]:
        """Pack pedalboard as compressed bundle"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via file_manager
            return {"success": False, "error": "Pack pedalboard bundle not implemented"}
        except Exception as e:
            logger.error("Failed to pack pedalboard bundle: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_pedalboard_bundle")
    async def handle_load_pedalboard_bundle(self, **kwargs) -> Dict[str, Any]:
        """Load pedalboard from bundle path"""
        try:
            bundlepath = kwargs.get("bundlepath")
            is_default = kwargs.get("is_default", "0")

            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Load pedalboard bundle not implemented"}
        except Exception as e:
            logger.error("Failed to load pedalboard bundle: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_pedalboard_web")
    async def handle_load_pedalboard_web(self, **kwargs) -> Dict[str, Any]:
        """Load pedalboard from uploaded file"""
        try:
            file_data = kwargs.get("file_data")
            filename = kwargs.get("filename")

            if not file_data or not filename:
                return {"success": False, "error": "Missing file data or filename"}

            # This would need to be implemented via file_manager and pedalboard_manager
            return {"success": False, "error": "Load pedalboard web not implemented"}
        except Exception as e:
            logger.error("Failed to load pedalboard web: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("factory_copy_pedalboard")
    async def handle_factory_copy_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Create user copy of factory pedalboard"""
        try:
            bundlepath = kwargs.get("bundlepath")
            title = kwargs.get("title")

            if not bundlepath or not title:
                return {"success": False, "error": "Missing 'bundlepath' or 'title' parameter"}

            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Factory copy pedalboard not implemented"}
        except Exception as e:
            logger.error("Failed to factory copy pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_pedalboard_info")
    async def handle_get_pedalboard_info(self, **kwargs) -> Dict[str, Any]:
        """Get pedalboard information without loading"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Get pedalboard info not implemented"}
        except Exception as e:
            logger.error("Failed to get pedalboard info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_pedalboard")
    async def handle_remove_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Remove/delete pedalboard"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via pedalboard_manager
            return {"success": False, "error": "Remove pedalboard not implemented"}
        except Exception as e:
            logger.error("Failed to remove pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_pedalboard_image")
    async def handle_get_pedalboard_image(self, **kwargs) -> Dict[str, Any]:
        """Get pedalboard screenshot or thumbnail image"""
        try:
            bundlepath = kwargs.get("bundlepath")
            image_type = kwargs.get("image_type", "screenshot")  # screenshot or thumbnail

            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via file_manager
            return {"success": False, "error": "Get pedalboard image not implemented"}
        except Exception as e:
            logger.error("Failed to get pedalboard image: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("generate_pedalboard_image")
    async def handle_generate_pedalboard_image(self, **kwargs) -> Dict[str, Any]:
        """Generate pedalboard screenshot"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via screenshot_manager
            return {"success": False, "error": "Generate pedalboard image not implemented"}
        except Exception as e:
            logger.error("Failed to generate pedalboard image: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("wait_pedalboard_image")
    async def handle_wait_pedalboard_image(self, **kwargs) -> Dict[str, Any]:
        """Wait for pedalboard screenshot generation"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via screenshot_manager
            return {"success": False, "error": "Wait pedalboard image not implemented"}
        except Exception as e:
            logger.error("Failed to wait pedalboard image: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("check_pedalboard_image")
    async def handle_check_pedalboard_image(self, **kwargs) -> Dict[str, Any]:
        """Check pedalboard screenshot generation status"""
        try:
            bundlepath = kwargs.get("bundlepath")
            if not bundlepath:
                return {"success": False, "error": "Missing 'bundlepath' parameter"}

            # This would need to be implemented via screenshot_manager
            return {"success": False, "error": "Check pedalboard image not implemented"}
        except Exception as e:
            logger.error("Failed to check pedalboard image: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("add_cv_addressing_port")
    async def handle_add_cv_addressing_port(self, **kwargs) -> Dict[str, Any]:
        """Add CV addressing plugin port"""
        try:
            uri = kwargs.get("uri")
            name = kwargs.get("name")

            if not uri or not name:
                return {"success": False, "error": "Missing 'uri' or 'name' parameter"}

            # This would need to be implemented via cv_addressing_manager
            return {"success": False, "error": "Add CV addressing port not implemented"}
        except Exception as e:
            logger.error("Failed to add CV addressing port: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_cv_addressing_port")
    async def handle_remove_cv_addressing_port(self, **kwargs) -> Dict[str, Any]:
        """Remove CV addressing plugin port"""
        try:
            uri = kwargs.get("uri")
            if not uri:
                return {"success": False, "error": "Missing 'uri' parameter"}

            # This would need to be implemented via cv_addressing_manager
            return {"success": False, "error": "Remove CV addressing port not implemented"}
        except Exception as e:
            logger.error("Failed to remove CV addressing port: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_transport_sync_mode")
    async def handle_set_transport_sync_mode(self, **kwargs) -> Dict[str, Any]:
        """Set transport synchronization mode"""
        try:
            mode = kwargs.get("mode")
            if not mode:
                return {"success": False, "error": "Missing 'mode' parameter"}

            # This would need to be implemented via transport_manager
            return {"success": False, "error": "Set transport sync mode not implemented"}
        except Exception as e:
            logger.error("Failed to set transport sync mode: %s", e)
            return {"success": False, "error": str(e)}

