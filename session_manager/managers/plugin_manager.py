"""
MOD UI - Audio Processing Service - Plugin Manager

Manages plugin instances, parameters, and state.
"""

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Localized pylint - best-effort publish calls use broad except handling
# pylint: disable=broad-except


@dataclass
class PluginInstance:
    """Represents a loaded plugin instance"""

    uri: str
    instance_id: str
    name: str
    brand: str
    version: str
    parameters: Dict[str, Any]
    ports: Dict[str, Any]
    available_parameters: Dict[str, Any]  # Available parameters from plugin essentials
    x: float = 0.0
    y: float = 0.0
    enabled: bool = True
    preset: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class PluginManager:
    """Manages plugin loading, unloading, and parameter control"""

    def __init__(self, bridge_client, zmq_service=None):
        self.bridge = bridge_client
        self.zmq_service = zmq_service
        self.instances: Dict[str, PluginInstance] = {}
        self.available_plugins: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize plugin manager"""
        logger.info("Initializing plugin manager")

        # Load available plugins
        await self._load_available_plugins()

        logger.info(
            "Plugin manager initialized with %s available plugins",
            len(self.available_plugins),
        )

    async def _publish_event(self, event_name: str, payload: Dict[str, Any]):
        """Publish an event to the ZMQ service (best-effort)."""
        if not self.zmq_service:
            return

        try:
            await self.zmq_service.publish_event(event_name, payload)
        except Exception:
            logger.debug("Failed to publish event %s", event_name)

    async def _load_available_plugins(self):
        """Load list of available plugins from bridge service"""
        try:
            # Get available plugins from bridge service
            result = await self.bridge.call("modhost_bridge", "get_available_plugins")

            # Check if we got plugins directly (successful response) or an error
            if "plugins" in result and not result.get("error"):
                self.available_plugins = result.get("plugins", {})
                logger.info("Loaded %d available plugins from bridge service", len(self.available_plugins))
            elif result.get("error"):
                logger.warning("Failed to get available plugins from bridge: %s", result.get("error"))
                # Fallback to empty dict
                self.available_plugins = {}
            else:
                logger.warning("Unexpected response format from bridge: %s", result)
                # Fallback to empty dict
                self.available_plugins = {}
        except Exception as e:
            logger.error("Error loading available plugins from bridge: %s", e)
            # Fallback to empty dict
            self.available_plugins = {}

    async def get_available_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available plugins"""
        return self.available_plugins.copy()

    async def load_plugin(
        self,
        uri: str,
        x: float = 0.0,
        y: float = 0.0,
        parameters: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Load a plugin instance"""
        async with self._lock:
            # Check if plugin exists
            if uri not in self.available_plugins:
                raise ValueError(f"Plugin not found: {uri}")

            plugin_info = self.available_plugins[uri]

            # Ask the bridge to create the instance. The bridge (C++ side)
            # generates its own canonical instance_id and returns it in the
            # response. Use that instance id so both components agree on the
            # identity of the plugin.
            result = await self.bridge.call(
                "modhost_bridge",
                "load_plugin",
                uri=uri,
                x=x,
                y=y,
                parameters=parameters or {},
            )

            # Check for error or missing instance id
            if "error" in result:
                raise RuntimeError(f"Failed to add plugin to bridge: {result.get('error', 'Unknown error')}")
            if not result.get("success", True):
                raise RuntimeError(f"Failed to add plugin to bridge: {result.get('error', 'Unknown error')}")

            instance_id = result.get("instance_id")
            if not instance_id:
                raise RuntimeError("Bridge did not return an instance_id for the loaded plugin")

            # Verify the bridge actually registered the instance. This avoids
            # transient races where the bridge may take a short moment to
            # publish the new instance internally. Poll get_plugin_info for a
            # short period (10 seconds) before giving up.
            verified = False
            max_attempts = 100
            for attempt in range(max_attempts):
                verify = await self.bridge.call("modhost_bridge", "get_plugin_info", instance_id=instance_id)
                if verify and not verify.get("error") and verify.get("success", True):
                    verified = True
                    break
                # small backoff
                await asyncio.sleep(0.1)

            if not verified:
                raise RuntimeError(f"Bridge did not register plugin instance within timeout: {instance_id}")

            # Get plugin essentials (parameters, etc.)
            essentials = await self.get_plugin_essentials(uri)
            logger.debug("Plugin essentials for %s: %s", uri, essentials)
            available_parameters = {}

            # The bridge may expose parameters under several keys depending on
            # the plugin scanner: 'parameters' (canonical), or LV2-specific
            # lists like 'control_inputs' / 'control_outputs'. Collect entries
            # from all likely locations and treat items with a symbol as valid
            # even if the 'valid' flag is missing.
            candidates = []
            if isinstance(essentials, dict):
                candidates.extend(essentials.get("parameters", []))
                candidates.extend(essentials.get("control_inputs", []))
                candidates.extend(essentials.get("control_outputs", []))

            for param in candidates:
                # If 'valid' is present, obey it; otherwise consider present
                # symbols as valid parameters
                has_symbol = bool(param.get("symbol") or param.get("name") or param.get("short_name"))
                is_valid = param.get("valid") if ("valid" in param) else has_symbol
                if not is_valid:
                    continue

                # Prefer explicit symbol, fall back to name/short_name/label
                param_symbol = param.get("symbol") or param.get("name") or param.get("short_name") or param.get("label")
                if param_symbol:
                    available_parameters[param_symbol] = param

            # Create plugin instance
            instance = PluginInstance(
                uri=uri,
                instance_id=instance_id,
                name=plugin_info.get("name", "Unknown"),
                brand=plugin_info.get("brand", "Unknown"),
                version=plugin_info.get("version", "1.0"),
                parameters=parameters or {},
                ports=plugin_info.get("ports", {}),
                available_parameters=available_parameters,
                x=x,
                y=y,
            )

            # Note: initial parameters were passed to the bridge when loading
            # the plugin; the bridge will apply them to the mod-host. Avoid
            # double-applying them here.

            # Store instance
            self.instances[instance_id] = instance

            # Publish event (support service bus API compatibility)
            # Best-effort publish; don't fail the operation on publish errors
            await self._publish_event(
                "plugin_loaded",
                {"instance_id": instance_id, "uri": uri, "name": instance.name},
            )

            logger.info("Loaded plugin %s as %s", uri, instance_id)

            # Convert to JSON-serializable dict (convert datetimes to isoformat)
            plugin_dict = asdict(instance)
            return {"instance_id": instance_id, "plugin": plugin_dict}

    async def unload_plugin(self, instance_id: str) -> Dict[str, Any]:
        """Unload a plugin instance"""
        async with self._lock:
            if instance_id not in self.instances:
                raise ValueError(f"Plugin instance not found: {instance_id}")

            instance = self.instances[instance_id]

            # Remove from bridge service
            result = await self.bridge.call("modhost_bridge", "unload_plugin", instance_id=instance_id)
            if not result.get("success", False):
                logger.warning("Failed to remove plugin %s from bridge: %s", instance_id, result.get("error", "Unknown error"))

            # Remove from instances
            del self.instances[instance_id]

            # Publish event (support service bus API compatibility)
            await self._publish_event(
                "plugin_unloaded", {"instance_id": instance_id, "uri": instance.uri}
            )

            logger.info("Unloaded plugin %s", instance_id)

            return {"status": "ok", "instance_id": instance_id}

    async def set_parameter(
        self, instance_id: str, parameter: str, value: float
    ) -> Dict[str, Any]:
        """Set plugin parameter"""
        if instance_id not in self.instances:
            raise ValueError(f"Plugin instance not found: {instance_id}")

        instance = self.instances[instance_id]

        # Validate parameter name
        if parameter not in instance.available_parameters:
            available_params = list(instance.available_parameters.keys())
            raise ValueError(f"Invalid parameter '{parameter}' for plugin {instance.uri}. Available parameters: {available_params}")

        # Set in bridge service
        result = await self.bridge.call("modhost_bridge", "set_parameter", instance_id=instance_id, parameter=parameter, value=value)
        if not result.get("success", False):
            raise RuntimeError(f"Failed to set parameter in bridge: {result.get('error', 'Unknown error')}")

        # Update local state
        instance.parameters[parameter] = value

        # Publish event (support service bus API compatibility)
        await self._publish_event(
            "parameter_changed",
            {"instance_id": instance_id, "parameter": parameter, "value": value},
        )

        logger.debug("Set parameter %s.%s = %s", instance_id, parameter, value)

        return {"status": "ok", "value": value}

    async def get_parameter(self, instance_id: str, parameter: str) -> Dict[str, Any]:
        """Get plugin parameter value"""
        if instance_id not in self.instances:
            raise ValueError(f"Plugin instance not found: {instance_id}")

        # Try to get from bridge service first
        result = await self.bridge.call("modhost_bridge", "get_parameter", instance_id=instance_id, parameter=parameter)
        if result.get("success", False):
            value = result.get("value")
        else:
            # Fallback to stored value
            instance = self.instances[instance_id]
            value = instance.parameters.get(parameter)

        return {"parameter": parameter, "value": value}

    async def get_plugin_info(self, instance_id: str) -> Dict[str, Any]:
        """Get plugin instance information"""
        if instance_id not in self.instances:
            raise ValueError(f"Plugin instance not found: {instance_id}")

        instance = self.instances[instance_id]
        return {"plugin": asdict(instance)}

    async def list_instances(self) -> Dict[str, Any]:
        """List all loaded plugin instances"""
        instances = {}
        for instance_id, instance in self.instances.items():
            instances[instance_id] = asdict(instance)

        return {"instances": instances}

    async def clear_all(self):
        """Unload all plugin instances"""
        instance_ids = list(self.instances.keys())
        for instance_id in instance_ids:
            try:
                await self.unload_plugin(instance_id)
            except Exception as e:
                logger.error("Error unloading plugin %s: %s", instance_id, e)

        logger.info("Cleared all plugin instances")

    async def shutdown(self):
        """Shutdown plugin manager"""
        logger.info("Shutting down plugin manager")
        await self.clear_all()
        logger.info("Plugin manager shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Get plugin manager status"""
        return {
            "loaded_instances": len(self.instances),
            "available_plugins": len(self.available_plugins),
            "instances": list(self.instances.keys()),
        }

    async def get_plugin_essentials(self, plugin_uri: str) -> Dict[str, Any]:
        """Get plugin essentials (parameters, ports, etc.)"""
        try:
            result = await self.bridge.call("modhost_bridge", "get_plugin_essentials", plugin_uri=plugin_uri)

            if "error" in result:
                raise RuntimeError(f"Failed to get plugin essentials: {result.get('error', 'Unknown error')}")

            return result.get("essentials", {})
        except Exception as e:
            logger.error("Error getting plugin essentials for %s: %s", plugin_uri, e)
            raise
