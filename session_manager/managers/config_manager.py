"""
ConfigManager: thin wrapper around the external config-service

Provides a small async API used by the session manager to get/set
configuration values via the existing ZMQService call mechanism.
"""
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Wraps calls to the `config_service` via the provided ZMQService.

    This class intentionally stays small: it forwards calls to the
    remote config service and normalizes error handling and timeouts.
    """

    def __init__(self, zmq_service, service_name: str = "config_service", timeout: float = 2.0):
        self.zmq = zmq_service
        self.service_name = service_name
        self.timeout = timeout

    async def get_setting(self, key: str) -> Optional[Any]:
        """Return the single setting value or None if not present."""
        try:
            result = await self.zmq.call(self.service_name, "get_setting", timeout=self.timeout, key=key)
            # result expected to be {'value': ...}
            if isinstance(result, dict) and "value" in result:
                return result["value"]
            return None
        except Exception as e:
            logger.error("ConfigManager.get_setting(%s) failed: %s", key, e)
            return None

    async def set_setting(self, key: str, value: Any) -> bool:
        """Set a single key/value and return True on success."""
        try:
            await self.zmq.call(self.service_name, "set_setting", timeout=self.timeout, key=key, value=value)
            return True
        except Exception as e:
            logger.error("ConfigManager.set_setting(%s) failed: %s", key, e)
            return False

    async def set_config(self, key: str, value: Any) -> bool:
        """Alias for set_setting kept for API clarity: set a config key to value."""
        return await self.set_setting(key, value)

    async def get_settings(self, queries: Dict[str, Any]) -> Dict[str, Any]:
        """Batch get: returns a dict of key->value (values may be None)."""
        try:
            result = await self.zmq.call(self.service_name, "get_settings", timeout=self.timeout, queries=queries)
            # Accept both {'results': {...}} or direct dict
            if isinstance(result, dict) and "results" in result and isinstance(result["results"], dict):
                return result["results"]
            if isinstance(result, dict):
                return result
            return {}
        except Exception as e:
            logger.error("ConfigManager.get_settings failed: %s", e)
            return {}

    async def set_settings(self, settings: Dict[str, Any]) -> bool:
        """Batch set multiple keys/values. Returns True on success."""
        try:
            await self.zmq.call(self.service_name, "set_settings", timeout=self.timeout, **settings)
            return True
        except Exception as e:
            logger.error("ConfigManager.set_settings failed: %s", e)
            return False

    async def reset_config(self) -> bool:
        """Reset configuration to empty/default. Implementation-defined."""
        try:
            # Try to set an empty dict at top level
            await self.zmq.call(self.service_name, "set_settings", timeout=self.timeout, **{})
            return True
        except Exception as e:
            logger.error("ConfigManager.reset_config failed: %s", e)
            return False
