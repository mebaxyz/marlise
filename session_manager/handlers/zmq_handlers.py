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

	# Connection management handlers
	@zmq_handler("create_connection")
	async def handle_create_connection(self, **kwargs) -> Dict[str, Any]:
		"""Create connection"""
		try:
			source = kwargs.get("source")
			target = kwargs.get("target")

			if not source or not target:
				return {"success": False, "error": "Missing 'source' or 'target' parameter"}

			await self.session_manager.create_connection(source, target)
			return {"success": True}
		except Exception as e:
			logger.error("Failed to create connection: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("remove_connection")
	async def handle_remove_connection(self, **kwargs) -> Dict[str, Any]:
		"""Remove connection"""
		try:
			source = kwargs.get("source")
			target = kwargs.get("target")

			if not source or not target:
				return {"success": False, "error": "Missing 'source' or 'target' parameter"}

			await self.session_manager.remove_connection(source, target)
			return {"success": True}
		except Exception as e:
			logger.error("Failed to remove connection: %s", e)
			return {"success": False, "error": str(e)}

	# Snapshot management handlers
	@zmq_handler("create_snapshot")
	async def handle_create_snapshot(self, **kwargs) -> Dict[str, Any]:
		"""Create snapshot"""
		try:
			name = kwargs.get("name")
			if not name:
				return {"success": False, "error": "Missing 'name' parameter"}

			snapshot = await self.session_manager.create_snapshot(name)
			return {"success": True, "snapshot": snapshot}
		except Exception as e:
			logger.error("Failed to create snapshot: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("apply_snapshot")
	async def handle_apply_snapshot(self, **kwargs) -> Dict[str, Any]:
		"""Apply snapshot"""
		try:
			name = kwargs.get("name")
			if not name:
				return {"success": False, "error": "Missing 'name' parameter"}

			await self.session_manager.apply_snapshot(name)
			return {"success": True}
		except Exception as e:
			logger.error("Failed to apply snapshot: %s", e)
			return {"success": False, "error": str(e)}

	# Utility handlers
	@zmq_handler("health_check")
	async def handle_health_check(self, **_kwargs) -> Dict[str, Any]:
		"""Health check"""
		try:
			# Check modhost bridge
			result = await self._call_bridge("health_check")
			modhost_status = result if (result and result.get("success", False)) else {"status": "error"}

			# Check plugin manager
			plugin_status = self.plugin_manager.get_status()

			# Check session manager
			session_status = self.session_manager.get_status()

			return {
				"success": True,
				"status": "healthy",
				"components": {
					"modhost_bridge": modhost_status,
					"plugin_manager": plugin_status,
					"session_manager": session_status,
				},
			}
		except Exception as e:
			logger.error("Health check failed: %s", e)
			return {"success": False, "error": str(e)}
	@zmq_handler("ping")
	async def handle_echo(self, **kwargs) -> Dict[str, Any]:
		"""Echo message (registered on the 'ping' event via @zmq_handler('ping')).
		"""
		return {"echo": kwargs.get("message", "")}

	# Phase 1 Critical mod-host command handlers
	@zmq_handler("activate_plugin")
	async def handle_activate_plugin(self, **kwargs) -> Dict[str, Any]:
		"""Activate plugin"""
		try:
			instance_id = kwargs.get("instance_id")
			if instance_id is None:
				return {"success": False, "error": "Missing 'instance_id' parameter"}

			result = await self._call_bridge("activate_plugin", instance_id=instance_id)
			return self._success_or_error(result, err_msg="Failed to activate plugin")
		except Exception as e:
			logger.error("Failed to activate plugin: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("preload_plugin")
	async def handle_preload_plugin(self, **kwargs) -> Dict[str, Any]:
		"""Preload plugin"""
		try:
			uri = kwargs.get("uri")
			if not uri:
				return {"success": False, "error": "Missing 'uri' parameter"}

			result = await self._call_bridge("preload_plugin", uri=uri)
			return self._success_or_error(result, err_msg="Failed to preload plugin")
		except Exception as e:
			logger.error("Failed to preload plugin: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("bypass_plugin")
	async def handle_bypass_plugin(self, **kwargs) -> Dict[str, Any]:
		"""Bypass plugin"""
		try:
			instance_id = kwargs.get("instance_id")
			bypass = kwargs.get("bypass", True)

			if instance_id is None:
				return {"success": False, "error": "Missing 'instance_id' parameter"}

			result = await self._call_bridge("bypass_plugin", instance_id=instance_id, bypass=bypass)
			return self._success_or_error(result, err_msg="Failed to bypass plugin")
		except Exception as e:
			logger.error("Failed to bypass plugin: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("disconnect_all_ports")
	async def handle_disconnect_all_ports(self, **kwargs) -> Dict[str, Any]:
		"""Disconnect all ports"""
		try:
			instance_id = kwargs.get("instance_id")
			if instance_id is None:
				return {"success": False, "error": "Missing 'instance_id' parameter"}

			result = await self._call_bridge("disconnect_all_ports", instance_id=instance_id)
			return self._success_or_error(result, err_msg="Failed to disconnect all ports")
		except Exception as e:
			logger.error("Failed to disconnect all ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_cpu_load")
	async def handle_get_cpu_load(self, **_kwargs) -> Dict[str, Any]:
		"""Get CPU load"""
		try:
			result = await self._call_bridge("get_cpu_load")
			if result and result.get("success", False):
				return {"success": True, "cpu_load": result.get("cpu_load")}
			return {"success": False, "error": "Failed to get CPU load"}
		except Exception as e:
			logger.error("Failed to get CPU load: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_max_cpu_load")
	async def handle_get_max_cpu_load(self, **_kwargs) -> Dict[str, Any]:
		"""Get max CPU load"""
		try:
			result = await self._call_bridge("get_max_cpu_load")
			if result and result.get("success", False):
				return {"success": True, "max_cpu_load": result.get("max_cpu_load")}
			return {"success": False, "error": "Failed to get max CPU load"}
		except Exception as e:
			logger.error("Failed to get max CPU load: %s", e)
			return {"success": False, "error": str(e)}

	# Phase 2 Preset Management handlers
	@zmq_handler("load_preset")
	async def handle_load_preset(self, **kwargs) -> Dict[str, Any]:
		"""Load preset"""
		try:
			instance_id = kwargs.get("instance_id")
			uri = kwargs.get("uri")
			label = kwargs.get("label")

			if instance_id is None or not uri or not label:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("load_preset", instance_id=instance_id, uri=uri, label=label)
			return self._success_or_error(result, err_msg="Failed to load preset")
		except Exception as e:
			logger.error("Failed to load preset: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("save_preset")
	async def handle_save_preset(self, **kwargs) -> Dict[str, Any]:
		"""Save preset"""
		try:
			instance_id = kwargs.get("instance_id")
			uri = kwargs.get("uri")
			label = kwargs.get("label")
			directory = kwargs.get("directory")

			if instance_id is None or not uri or not label or not directory:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("save_preset", instance_id=instance_id, uri=uri, label=label, directory=directory)
			return self._success_or_error(result, err_msg="Failed to save preset")
		except Exception as e:
			logger.error("Failed to save preset: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("show_presets")
	async def handle_show_presets(self, **kwargs) -> Dict[str, Any]:
		"""Show presets"""
		try:
			uri = kwargs.get("uri")
			if not uri:
				return {"success": False, "error": "Missing 'uri' parameter"}

			result = await self._call_bridge("show_presets", uri=uri)
			if result and result.get("success", False):
				return {"success": True, "presets": result.get("presets", [])}
			return {"success": False, "error": "Failed to show presets"}
		except Exception as e:
			logger.error("Failed to show presets: %s", e)
			return {"success": False, "error": str(e)}

	# Phase 3 Monitoring handlers
	@zmq_handler("monitor_parameter")
	async def handle_monitor_parameter(self, **kwargs) -> Dict[str, Any]:
		"""Monitor parameter"""
		try:
			instance_id = kwargs.get("instance_id")
			port = kwargs.get("port")
			monitor = kwargs.get("monitor", True)

			if instance_id is None or port is None:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("monitor_parameter", instance_id=instance_id, port=port, monitor=monitor)
			return self._success_or_error(result, err_msg="Failed to monitor parameter")
		except Exception as e:
			logger.error("Failed to monitor parameter: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("monitor_output")
	async def handle_monitor_output(self, **kwargs) -> Dict[str, Any]:
		"""Monitor output"""
		try:
			instance_id = kwargs.get("instance_id")
			port = kwargs.get("port")
			monitor = kwargs.get("monitor", True)

			if instance_id is None or port is None:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("monitor_output", instance_id=instance_id, port=port, monitor=monitor)
			return self._success_or_error(result, err_msg="Failed to monitor output")
		except Exception as e:
			logger.error("Failed to monitor output: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_audio_levels")
	async def handle_get_audio_levels(self, **_kwargs) -> Dict[str, Any]:
		"""Get audio levels"""
		try:
			result = await self._call_bridge("get_audio_levels")
			if result and result.get("success", False):
				return {"success": True, "levels": result.get("levels", {})}
			return {"success": False, "error": "Failed to get audio levels"}
		except Exception as e:
			logger.error("Failed to get audio levels: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("flush_parameters")
	async def handle_flush_parameters(self, **_kwargs) -> Dict[str, Any]:
		"""Flush parameters"""
		try:
			result = await self._call_bridge("flush_parameters")
			return self._success_or_error(result, err_msg="Failed to flush parameters")
		except Exception as e:
			logger.error("Failed to flush parameters: %s", e)
			return {"success": False, "error": str(e)}

	# Phase 4 Patch Management handlers
	@zmq_handler("set_patch_property")
	async def handle_set_patch_property(self, **kwargs) -> Dict[str, Any]:
		"""Set patch property"""
		try:
			instance_id = kwargs.get("instance_id")
			property_name = kwargs.get("property")
			value = kwargs.get("value")

			if instance_id is None or not property_name or value is None:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("set_patch_property", instance_id=instance_id, property_name=property_name, value=value)
			return self._success_or_error(result, err_msg="Failed to set patch property")
		except Exception as e:
			logger.error("Failed to set patch property: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_patch_property")
	async def handle_get_patch_property(self, **kwargs) -> Dict[str, Any]:
		"""Get patch property"""
		try:
			instance_id = kwargs.get("instance_id")
			property_name = kwargs.get("property")

			if instance_id is None or not property_name:
				return {"success": False, "error": "Missing required parameters"}

			result = await self._call_bridge("get_patch_property", instance_id=instance_id, property_name=property_name)
			if result and result.get("success", False):
				return {"success": True, "value": result.get("value")}
			return {"success": False, "error": "Failed to get patch property"}
		except Exception as e:
			logger.error("Failed to get patch property: %s", e)
			return {"success": False, "error": str(e)}

	# Phase 5 Bundle Management handlers
	# Add bundle handlers here if needed

	# Audio System Management handlers
	@zmq_handler("init_jack")
	async def handle_init_jack(self, **_kwargs) -> Dict[str, Any]:
		"""Initialize JACK audio system"""
		try:
			result = await self._call_bridge("init_jack")
			return self._success_or_error(result, err_msg="Failed to initialize JACK")
		except Exception as e:
			logger.error("Failed to initialize JACK: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("close_jack")
	async def handle_close_jack(self, **_kwargs) -> Dict[str, Any]:
		"""Close JACK audio system"""
		try:
			result = await self._call_bridge("close_jack")
			return self._success_or_error(result, err_msg="Failed to close JACK")
		except Exception as e:
			logger.error("Failed to close JACK: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_jack_data")
	async def handle_get_jack_data(self, **kwargs) -> Dict[str, Any]:
		"""Get JACK audio system data"""
		try:
			with_transport = kwargs.get("with_transport", False)
			result = await self._call_bridge("get_jack_data", with_transport=with_transport)
			if result and result.get("success", False):
				return {
					"success": True,
					"cpu_load": result.get("cpu_load"),
					"xruns": result.get("xruns"),
					"rolling": result.get("rolling"),
					"bpb": result.get("bpb"),
					"bpm": result.get("bpm"),
				}
			return {"success": False, "error": "Failed to get JACK data"}
		except Exception as e:
			logger.error("Failed to get JACK data: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_jack_buffer_size")
	async def handle_get_jack_buffer_size(self, **_kwargs) -> Dict[str, Any]:
		"""Get JACK buffer size"""
		try:
			result = await self._call_bridge("get_jack_buffer_size")
			return self._success_or_error(result, ok_map={"buffer_size": "buffer_size"}, err_msg="Failed to get buffer size")
		except Exception as e:
			logger.error("Failed to get JACK buffer size: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("set_jack_buffer_size")
	async def handle_set_jack_buffer_size(self, **kwargs) -> Dict[str, Any]:
		"""Set JACK buffer size"""
		try:
			size = kwargs.get("size")
			if size is None:
				return {"success": False, "error": "Missing 'size' parameter"}
			result = await self._call_bridge("set_jack_buffer_size", size=size)
			return self._success_or_error(result, ok_map={"buffer_size": "buffer_size"}, err_msg="Failed to set buffer size")
		except Exception as e:
			logger.error("Failed to set JACK buffer size: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_jack_sample_rate")
	async def handle_get_jack_sample_rate(self, **_kwargs) -> Dict[str, Any]:
		"""Get JACK sample rate"""
		try:
			result = await self._call_bridge("get_jack_sample_rate")
			return self._success_or_error(result, ok_map={"sample_rate": "sample_rate"}, err_msg="Failed to get sample rate")
		except Exception as e:
			logger.error("Failed to get JACK sample rate: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_jack_port_alias")
	async def handle_get_jack_port_alias(self, **kwargs) -> Dict[str, Any]:
		"""Get JACK port alias"""
		try:
			port_name = kwargs.get("port_name")
			if not port_name:
				return {"success": False, "error": "Missing 'port_name' parameter"}

			result = await self._call_bridge("get_jack_port_alias", port_name=port_name)
			if result and result.get("success", False):
				return {"success": True, "alias": result.get("alias")}
			return {"success": False, "error": "Failed to get port alias"}
		except Exception as e:
			logger.error("Failed to get JACK port alias: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_jack_hardware_ports")
	async def handle_get_jack_hardware_ports(self, **kwargs) -> Dict[str, Any]:
		"""Get JACK hardware ports"""
		try:
			is_audio = kwargs.get("is_audio", True)
			is_output = kwargs.get("is_output", False)

			result = await self._call_bridge("get_jack_hardware_ports", is_audio=is_audio, is_output=is_output)
			if result and result.get("success", False):
				return {"success": True, "ports": result.get("ports", [])}
			return {"success": False, "error": "Failed to get hardware ports"}
		except Exception as e:
			logger.error("Failed to get JACK hardware ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_midi_beat_clock_sender_port")
	async def handle_has_midi_beat_clock_sender_port(self, **_kwargs) -> Dict[str, Any]:
		"""Check if MIDI beat clock sender port exists"""
		try:
			result = await self._call_bridge("has_midi_beat_clock_sender_port")
			if result and result.get("success", False):
				return {"success": True, "has_port": result.get("has_port", False)}
			return {"success": False, "error": "Failed to check MIDI beat clock sender port"}
		except Exception as e:
			logger.error("Failed to check MIDI beat clock sender port: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_serial_midi_input_port")
	async def handle_has_serial_midi_input_port(self, **_kwargs) -> Dict[str, Any]:
		"""Check if serial MIDI input port exists"""
		try:
			result = await self._call_bridge("has_serial_midi_input_port")
			if result and result.get("success", False):
				return {"success": True, "has_port": result.get("has_port", False)}
			return {"success": False, "error": "Failed to check serial MIDI input port"}
		except Exception as e:
			logger.error("Failed to check serial MIDI input port: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_serial_midi_output_port")
	async def handle_has_serial_midi_output_port(self, **_kwargs) -> Dict[str, Any]:
		"""Check if serial MIDI output port exists"""
		try:
			result = await self._call_bridge("has_serial_midi_output_port")
			if result and result.get("success", False):
				return {"success": True, "has_port": result.get("has_port", False)}
			return {"success": False, "error": "Failed to check serial MIDI output port"}
		except Exception as e:
			logger.error("Failed to check serial MIDI output port: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_midi_merger_output_port")
	async def handle_has_midi_merger_output_port(self, **_kwargs) -> Dict[str, Any]:
		"""Check if MIDI merger output port exists"""
		try:
			result = await self._call_bridge("has_midi_merger_output_port")
			if result and result.get("success", False):
				return {"success": True, "has_port": result.get("has_port", False)}
			return {"success": False, "error": "Failed to check MIDI merger output port"}
		except Exception as e:
			logger.error("Failed to check MIDI merger output port: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_midi_broadcaster_input_port")
	async def handle_has_midi_broadcaster_input_port(self, **_kwargs) -> Dict[str, Any]:
		"""Check if MIDI broadcaster input port exists"""
		try:
			result = await self._call_bridge("has_midi_broadcaster_input_port")
			if result and result.get("success", False):
				return {"success": True, "has_port": result.get("has_port", False)}
			return {"success": False, "error": "Failed to check MIDI broadcaster input port"}
		except Exception as e:
			logger.error("Failed to check MIDI broadcaster input port: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("has_duox_split_spdif")
	async def handle_has_duox_split_spdif(self, **_kwargs) -> Dict[str, Any]:
		"""Check if DuoX S/PDIF split feature exists"""
		try:
			result = await self._call_bridge("has_duox_split_spdif")
			if result and result.get("success", False):
				return {"success": True, "has_feature": result.get("has_feature", False)}
			return {"success": False, "error": "Failed to check DuoX S/PDIF split feature"}
		except Exception as e:
			logger.error("Failed to check DuoX S/PDIF split feature: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("connect_jack_ports")
	async def handle_connect_jack_ports(self, **kwargs) -> Dict[str, Any]:
		"""Connect JACK ports"""
		try:
			port1 = kwargs.get("port1")
			port2 = kwargs.get("port2")

			if not port1 or not port2:
				return {"success": False, "error": "Missing 'port1' or 'port2' parameter"}
			result = await self._call_bridge("connect_jack_ports", port1=port1, port2=port2)
			return self._success_or_error(result, err_msg="Failed to connect JACK ports")
		except Exception as e:
			logger.error("Failed to connect JACK ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("connect_jack_midi_output_ports")
	async def handle_connect_jack_midi_output_ports(self, **kwargs) -> Dict[str, Any]:
		"""Connect JACK MIDI output ports"""
		try:
			port = kwargs.get("port")
			if not port:
				return {"success": False, "error": "Missing 'port' parameter"}

			result = await self._call_bridge("connect_jack_midi_output_ports", port=port)
			return self._success_or_error(result, err_msg="Failed to connect JACK MIDI output ports")
		except Exception as e:
			logger.error("Failed to connect JACK MIDI output ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("disconnect_jack_ports")
	async def handle_disconnect_jack_ports(self, **kwargs) -> Dict[str, Any]:
		"""Disconnect JACK ports"""
		try:
			port1 = kwargs.get("port1")
			port2 = kwargs.get("port2")

			if not port1 or not port2:
				return {"success": False, "error": "Missing 'port1' or 'port2' parameter"}
			result = await self._call_bridge("disconnect_jack_ports", port1=port1, port2=port2)
			return self._success_or_error(result, err_msg="Failed to disconnect JACK ports")
		except Exception as e:
			logger.error("Failed to disconnect JACK ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("disconnect_all_jack_ports")
	async def handle_disconnect_all_jack_ports(self, **kwargs) -> Dict[str, Any]:
		"""Disconnect all JACK ports for a given port"""
		try:
			port = kwargs.get("port")
			if not port:
				return {"success": False, "error": "Missing 'port' parameter"}
			result = await self._call_bridge("disconnect_all_jack_ports", port=port)
			return self._success_or_error(result, err_msg="Failed to disconnect all JACK ports")
		except Exception as e:
			logger.error("Failed to disconnect all JACK ports: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("reset_xruns")
	async def handle_reset_xruns(self, **_kwargs) -> Dict[str, Any]:
		"""Reset JACK xruns counter"""
		try:
			result = await self._call_bridge("reset_xruns")
			return self._success_or_error(result, err_msg="Failed to reset xruns")
		except Exception as e:
			logger.error("Failed to reset xruns: %s", e)
			return {"success": False, "error": str(e)}

	# Missing plugin management methods from MESSAGE_SCHEMAS.md

	@zmq_handler("clear_all")
	async def handle_clear_all(self, **_kwargs) -> Dict[str, Any]:
		"""Clear all plugins"""
		try:
			result = await self._call_bridge("clear_all")
			return self._success_or_error(result, err_msg="Failed to clear all plugins")
		except Exception as e:
			logger.error("Failed to clear all plugins: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("search_plugins")
	async def handle_search_plugins(self, **kwargs) -> Dict[str, Any]:
		"""Search plugins with criteria"""
		try:
			query = kwargs.get("query", "")
			criteria = kwargs.get("criteria", {})
			result = await self._call_bridge("search_plugins", query=query, criteria=criteria)
			if result and result.get("success", False):
				return {"success": True, "plugins": result.get("plugins", [])}
			return {"success": False, "error": "Failed to search plugins"}
		except Exception as e:
			logger.error("Failed to search plugins: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_plugin_presets")
	async def handle_get_plugin_presets(self, **kwargs) -> Dict[str, Any]:
		"""Get presets for a plugin"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			if not plugin_uri:
				return {"success": False, "error": "Missing plugin_uri parameter"}

			result = await self._call_bridge("get_plugin_presets", plugin_uri=plugin_uri)
			if result and result.get("success", False):
				return {"success": True, "presets": result.get("presets", [])}
			return {"success": False, "error": "Failed to get plugin presets"}
		except Exception as e:
			logger.error("Failed to get plugin presets: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("validate_preset")
	async def handle_validate_preset(self, **kwargs) -> Dict[str, Any]:
		"""Validate a preset"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			preset_uri = kwargs.get("preset_uri", "")
			if not plugin_uri or not preset_uri:
				return {"success": False, "error": "Missing plugin_uri or preset_uri parameter"}

			result = await self._call_bridge("validate_preset", plugin_uri=plugin_uri, preset_uri=preset_uri)
			if result and result.get("success", False):
				return {"success": True, "valid": result.get("valid", False)}
			return {"success": False, "error": "Failed to validate preset"}
		except Exception as e:
			logger.error("Failed to validate preset: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("rescan_plugins")
	async def handle_rescan_plugins(self, **_kwargs) -> Dict[str, Any]:
		"""Rescan plugins"""
		try:
			result = await self._call_bridge("rescan_plugins")
			return self._success_or_error(result, err_msg="Failed to rescan plugins")
		except Exception as e:
			logger.error("Failed to rescan plugins: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("rescan_presets")
	async def handle_rescan_presets(self, **kwargs) -> Dict[str, Any]:
		"""Rescan presets for a plugin"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			result = await self._call_bridge("rescan_presets", plugin_uri=plugin_uri)
			return self._success_or_error(result, err_msg="Failed to rescan presets")
		except Exception as e:
			logger.error("Failed to rescan presets: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_plugin_gui")
	async def handle_get_plugin_gui(self, **kwargs) -> Dict[str, Any]:
		"""Get plugin GUI information"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			if not plugin_uri:
				return {"success": False, "error": "Missing plugin_uri parameter"}

			result = await self._call_bridge("get_plugin_gui", plugin_uri=plugin_uri)
			if result and result.get("success", False):
				return {"success": True, "gui": result.get("gui", {})}
			return {"success": False, "error": "Failed to get plugin GUI"}
		except Exception as e:
			logger.error("Failed to get plugin GUI: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_plugin_gui_mini")
	async def handle_get_plugin_gui_mini(self, **kwargs) -> Dict[str, Any]:
		"""Get plugin GUI mini information"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			if not plugin_uri:
				return {"success": False, "error": "Missing plugin_uri parameter"}

			result = await self._call_bridge("get_plugin_gui_mini", plugin_uri=plugin_uri)
			if result and result.get("success", False):
				return {"success": True, "gui_mini": result.get("gui_mini", {})}
			return {"success": False, "error": "Failed to get plugin GUI mini"}
		except Exception as e:
			logger.error("Failed to get plugin GUI mini: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("get_plugin_essentials")
	async def handle_get_plugin_essentials(self, **kwargs) -> Dict[str, Any]:
		"""Get plugin essentials"""
		try:
			plugin_uri = kwargs.get("plugin_uri", "")
			if not plugin_uri:
				return {"success": False, "error": "Missing plugin_uri parameter"}

			result = await self._call_bridge("get_plugin_essentials", plugin_uri=plugin_uri)
			if result and result.get("success", False):
				return {"success": True, "essentials": result.get("essentials", {})}
			return {"success": False, "error": "Failed to get plugin essentials"}
		except Exception as e:
			logger.error("Failed to get plugin essentials: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("is_bundle_loaded")
	async def handle_is_bundle_loaded(self, **kwargs) -> Dict[str, Any]:
		"""Check if bundle is loaded"""
		try:
			bundle_path = kwargs.get("bundle_path", "")
			if not bundle_path:
				return {"success": False, "error": "Missing bundle_path parameter"}

			result = await self._call_bridge("is_bundle_loaded", bundle_path=bundle_path)
			if result and result.get("success", False):
				return {"success": True, "loaded": result.get("loaded", False)}
			return {"success": False, "error": "Failed to check bundle status"}
		except Exception as e:
			logger.error("Failed to check bundle status: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("add_bundle")
	async def handle_add_bundle(self, **kwargs) -> Dict[str, Any]:
		"""Add a bundle"""
		try:
			bundle_path = kwargs.get("bundle_path", "")
			if not bundle_path:
				return {"success": False, "error": "Missing bundle_path parameter"}

			result = await self._call_bridge("add_bundle", bundle_path=bundle_path)
			return self._success_or_error(result, err_msg="Failed to add bundle")
		except Exception as e:
			logger.error("Failed to add bundle: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("remove_bundle")
	async def handle_remove_bundle(self, **kwargs) -> Dict[str, Any]:
		"""Remove a bundle"""
		try:
			bundle_path = kwargs.get("bundle_path", "")
			resource_path = kwargs.get("resource_path", "")
			if not bundle_path:
				return {"success": False, "error": "Missing bundle_path parameter"}

			result = await self._call_bridge("remove_bundle", bundle_path=bundle_path, resource_path=resource_path)
			return self._success_or_error(result, err_msg="Failed to remove bundle")
		except Exception as e:
			logger.error("Failed to remove bundle: %s", e)
			return {"success": False, "error": str(e)}

	@zmq_handler("list_bundle_plugins")
	async def handle_list_bundle_plugins(self, **kwargs) -> Dict[str, Any]:
		"""List plugins in a bundle"""
		try:
			bundle_path = kwargs.get("bundle_path", "")
			if not bundle_path:
				return {"success": False, "error": "Missing bundle_path parameter"}

			result = await self._call_bridge("list_bundle_plugins", bundle_path=bundle_path)
			if result and result.get("success", False):
				return {"success": True, "plugins": result.get("plugins", [])}
			return {"success": False, "error": "Failed to list bundle plugins"}
		except Exception as e:
			logger.error("Failed to list bundle plugins: %s", e)
			return {"success": False, "error": str(e)}
