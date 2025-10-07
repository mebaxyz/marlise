"""Service responsible for pedalboard lifecycle: create, load, save, snapshots."""
from dataclasses import asdict
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.pedalboard import Pedalboard
from ..models.connection import Connection
from ..managers.connection_manager import ConnectionManager
from ..infrastructure.utils import serialize_pedalboard
from ..infrastructure.storage import save_pedalboard

logger = logging.getLogger(__name__)


class PedalboardService:
    """Manages a pedalboard instance and persistence.

    Does not directly interact with the modhost bridge; it uses a provided
    plugin_manager and audio_system to load plugins and create connections.
    """

    def __init__(self, plugin_manager, bridge_client, zmq_service=None):
        self.plugin_manager = plugin_manager
        self.bridge = bridge_client
        self.zmq_service = zmq_service

        self.current_pedalboard: Optional[Pedalboard] = None
        self.connections = ConnectionManager([])

    async def create_pedalboard(self, name: str, description: str = "") -> Dict[str, Any]:
        pedalboard_id = str(uuid.uuid4())
        
        # Get available system inputs and outputs
        system_inputs, system_outputs = await self._discover_system_ports()
        
        pb = Pedalboard(
            id=pedalboard_id,
            name=name,
            description=description,
            plugins=[],
            connections=[],
            created_at=datetime.now(),
            modified_at=datetime.now(),
            metadata={},
            system_inputs=system_inputs,
            system_outputs=system_outputs,
        )

        # reset state
        self.current_pedalboard = pb
        self.connections = ConnectionManager([])

        if self.zmq_service:
            await self.zmq_service.publish_event("pedalboard_created", {"id": pedalboard_id, "name": name, "description": description})

        logger.info("Created pedalboard: %s (%s) with inputs: %s, outputs: %s", name, pedalboard_id, system_inputs, system_outputs)
        return {"pedalboard_id": pedalboard_id, "pedalboard": serialize_pedalboard(pb) if pb else {"pedalboard": None}}

    async def load_pedalboard(self, pedalboard_data: Dict[str, Any]) -> Dict[str, Any]:
        # Create pedalboard object
        pedalboard = Pedalboard(
            id=pedalboard_data.get("id", str(uuid.uuid4())),
            name=pedalboard_data.get("name", "Untitled"),
            description=pedalboard_data.get("description", ""),
            plugins=pedalboard_data.get("plugins", []),
            connections=[Connection(**conn) if isinstance(conn, dict) else conn for conn in pedalboard_data.get("connections", [])],
            created_at=datetime.fromisoformat(pedalboard_data.get("created_at", datetime.now().isoformat())),
            modified_at=datetime.now(),
            metadata=pedalboard_data.get("metadata", {}),
            system_inputs=pedalboard_data.get("system_inputs"),
            system_outputs=pedalboard_data.get("system_outputs"),
        )

        # --- System I/O validation & reconciliation ---------------------------------
        # Always discover current hardware ports and validate against what was saved.
        current_inputs, current_outputs = await self._discover_system_ports()
        saved_inputs = pedalboard.system_inputs or []
        saved_outputs = pedalboard.system_outputs or []
        io_validation = self._validate_system_io(saved_inputs, saved_outputs, current_inputs, current_outputs)

        # Apply resolved I/O (may keep saved or replace with current depending on strategy)
        pedalboard.system_inputs = io_validation["resolved_inputs"]
        pedalboard.system_outputs = io_validation["resolved_outputs"]

        if io_validation["changed"]:
            logger.warning(
                "System I/O mismatch on load: strategy=%s missing_inputs=%s missing_outputs=%s",
                io_validation["strategy"], io_validation["missing_inputs"], io_validation["missing_outputs"],
            )
            if self.zmq_service:
                # Publish a concise event so UI/clients can react
                await self.zmq_service.publish_event(
                    "system_io_validation",
                    {
                        "pedalboard_id": pedalboard.id,
                        "strategy": io_validation["strategy"],
                        "missing_inputs": io_validation["missing_inputs"],
                        "missing_outputs": io_validation["missing_outputs"],
                        "resolved_inputs": io_validation["resolved_inputs"],
                        "resolved_outputs": io_validation["resolved_outputs"],
                    },
                )
        else:
            inputs_count = len(pedalboard.system_inputs) if pedalboard.system_inputs else 0
            outputs_count = len(pedalboard.system_outputs) if pedalboard.system_outputs else 0
            logger.debug(
                "System I/O validated: no changes required (%s inputs / %s outputs)",
                inputs_count,
                outputs_count,
            )

        loaded_plugins = []
        plugin_mapping = {}
        for plugin_config in pedalboard.plugins:
            try:
                result = await self.plugin_manager.load_plugin(
                    uri=plugin_config["uri"],
                    x=plugin_config.get("x", 0.0),
                    y=plugin_config.get("y", 0.0),
                    parameters=plugin_config.get("parameters", {}),
                )
                old_id = plugin_config.get("instance_id")
                new_id = result["instance_id"]
                if old_id:
                    plugin_mapping[old_id] = new_id
                loaded_plugins.append({**plugin_config, "instance_id": new_id})
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", plugin_config.get("uri"), e)

        loaded_connections: List[Connection] = []
        for connection in pedalboard.connections:
            try:
                source_plugin = plugin_mapping.get(connection.source_plugin, connection.source_plugin)
                target_plugin = plugin_mapping.get(connection.target_plugin, connection.target_plugin)
                result = await self.bridge.call("modhost_bridge", "create_connection", source_plugin=source_plugin, source_port=connection.source_port, target_plugin=target_plugin, target_port=connection.target_port)
                if result.get("success", False):
                    new_connection = Connection(source_plugin=source_plugin, source_port=connection.source_port, target_plugin=target_plugin, target_port=connection.target_port)
                    loaded_connections.append(new_connection)
                else:
                    logger.error("Failed to create connection: %s", result.get("error", "Unknown error"))
            except Exception as e:
                logger.error("Failed to create connection: %s", e)

        pedalboard.plugins = loaded_plugins
        pedalboard.connections = loaded_connections

        self.current_pedalboard = pedalboard
        self.connections = ConnectionManager(loaded_connections)

        # Setup system I/O connections if plugins are loaded
        io_result = {"system_io_connections": []}
        if loaded_plugins:
            io_result = await self.setup_system_io_connections()

        if self.zmq_service:
            await self.zmq_service.publish_event("pedalboard_loaded", {
                "id": pedalboard.id, 
                "name": pedalboard.name, 
                "plugins_loaded": len(loaded_plugins), 
                "connections_created": len(loaded_connections),
                "system_io_setup": io_result.get("status", "skipped")
            })

        logger.info("Loaded pedalboard: %s (%s) with system I/O: %s", pedalboard.name, pedalboard.id, io_result.get("status", "skipped"))
        return {
            "status": "ok", 
            "pedalboard": serialize_pedalboard(pedalboard) if pedalboard else {"pedalboard": None}, 
            "plugins_loaded": len(loaded_plugins), 
            "connections_created": len(loaded_connections),
            "system_io": io_result
        }

    async def save_pedalboard(self) -> Dict[str, Any]:
        if not self.current_pedalboard:
            raise ValueError("No pedalboard currently loaded")

        self.current_pedalboard.modified_at = datetime.now()
        current_plugins = [asdict(instance) for instance in self.plugin_manager.instances.values()]
        self.current_pedalboard.plugins = current_plugins
        self.current_pedalboard.connections = self.connections.all()

        try:
            pb_dict = serialize_pedalboard(self.current_pedalboard) if self.current_pedalboard else {"pedalboard": None}
            pb_id, path = save_pedalboard(pb_dict)
        except Exception as e:
            logger.error("Failed to persist pedalboard: %s", e)
            raise

        if self.zmq_service:
            await self.zmq_service.publish_event("pedalboard_saved", {"id": self.current_pedalboard.id, "name": self.current_pedalboard.name, "saved_path": path})

        logger.info("Saved pedalboard: %s -> %s", self.current_pedalboard.name, path)
        return {"status": "ok", "pedalboard": serialize_pedalboard(self.current_pedalboard) if self.current_pedalboard else {"pedalboard": None}, "saved_id": pb_id, "saved_path": path}

    async def get_current_pedalboard(self, *, persist: bool = True) -> Dict[str, Any]:
        """Return current pedalboard. If persist is True (default) it triggers a save.

        Offline/demo usage can set persist=False to avoid disk writes.
        """
        if not self.current_pedalboard:
            return {"pedalboard": None}
        if persist:
            await self.save_pedalboard()
        return {"pedalboard": serialize_pedalboard(self.current_pedalboard) if self.current_pedalboard else {"pedalboard": None}}

    async def create_snapshot(self, name: str) -> Dict[str, Any]:
        if not self.current_pedalboard:
            raise ValueError("No pedalboard currently loaded")
        snapshot = {"id": str(uuid.uuid4()), "name": name, "created_at": datetime.now().isoformat(), "pedalboard_id": self.current_pedalboard.id, "plugin_states": {}}
        for inst_id, instance in self.plugin_manager.instances.items():
            snapshot["plugin_states"][inst_id] = instance.parameters.copy()
        return {"status": "ok", "snapshot": snapshot}

    async def apply_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        if not self.current_pedalboard:
            raise ValueError("No pedalboard currently loaded")
        applied_params = 0
        for instance_id, parameters in snapshot.get("plugin_states", {}).items():
            if instance_id in self.plugin_manager.instances:
                for param, value in parameters.items():
                    try:
                        await self.plugin_manager.set_parameter(instance_id, param, value)
                        applied_params += 1
                    except Exception as e:
                        logger.error("Failed to apply parameter %s.%s: %s", instance_id, param, e)
        if self.zmq_service:
            await self.zmq_service.publish_event("snapshot_applied", {"snapshot_id": snapshot.get("id"), "snapshot_name": snapshot.get("name"), "parameters_applied": applied_params})
        return {"status": "ok", "parameters_applied": applied_params}

    async def _discover_system_ports(self) -> tuple[list[str], list[str]]:
        """Discover available system input and output ports."""
        try:
            # Get system input ports (captures)
            inputs_result = await self.bridge.call("modhost_bridge", "get_jack_hardware_ports", is_audio=True, is_output=False)
            system_inputs = inputs_result.get("ports", []) if inputs_result.get("success") else []
            
            # Get system output ports (playbacks)  
            outputs_result = await self.bridge.call("modhost_bridge", "get_jack_hardware_ports", is_audio=True, is_output=True)
            system_outputs = outputs_result.get("ports", []) if outputs_result.get("success") else []
            
            # Default to standard stereo if discovery fails
            if not system_inputs:
                system_inputs = ["system:capture_1", "system:capture_2"]
            if not system_outputs:
                system_outputs = ["system:playback_1", "system:playback_2"]
                
            return system_inputs, system_outputs
            
        except Exception as e:
            logger.warning("Failed to discover system ports, using defaults: %s", e)
            return ["system:capture_1", "system:capture_2"], ["system:playback_1", "system:playback_2"]

    async def setup_system_io_connections(self) -> Dict[str, Any]:
        """Create connections from system inputs to first plugin and last plugin to system outputs."""
        if not self.current_pedalboard:
            return {"status": "error", "message": "No pedalboard loaded"}
            
        if not self.current_pedalboard.plugins:
            return {"status": "ok", "message": "No plugins loaded, no I/O connections needed"}
        
        created_connections = []
        failed_connections = []
        
        # Get first and last plugins in the chain
        first_plugin = self.current_pedalboard.plugins[0]
        last_plugin = self.current_pedalboard.plugins[-1]
        
        system_inputs = self.current_pedalboard.get_system_inputs()
        system_outputs = self.current_pedalboard.get_system_outputs()
        
        # Connect system inputs to first plugin
        for i, system_input in enumerate(system_inputs[:2]):  # Limit to stereo
            try:
                target_port = f"in_{i+1}" if i < len(system_inputs) else "in_1"
                result = await self.bridge.call("modhost_bridge", "connect_jack_ports", 
                                              port1=system_input, 
                                              port2=f"{first_plugin['instance_id']}:{target_port}")
                if result.get("success"):
                    created_connections.append(f"{system_input} -> {first_plugin['instance_id']}:{target_port}")
                else:
                    failed_connections.append(f"{system_input} -> {first_plugin['instance_id']}:{target_port}")
            except Exception as e:
                logger.error("Failed to connect system input %s: %s", system_input, e)
                failed_connections.append(f"{system_input} (error: {e})")
        
        # Connect last plugin to system outputs
        for i, system_output in enumerate(system_outputs[:2]):  # Limit to stereo
            try:
                source_port = f"out_{i+1}" if i < len(system_outputs) else "out_1"
                result = await self.bridge.call("modhost_bridge", "connect_jack_ports",
                                              port1=f"{last_plugin['instance_id']}:{source_port}",
                                              port2=system_output)
                if result.get("success"):
                    created_connections.append(f"{last_plugin['instance_id']}:{source_port} -> {system_output}")
                else:
                    failed_connections.append(f"{last_plugin['instance_id']}:{source_port} -> {system_output}")
            except Exception as e:
                logger.error("Failed to connect system output %s: %s", system_output, e)
                failed_connections.append(f"{system_output} (error: {e})")
        
        logger.info("System I/O setup: %d connections created, %d failed", len(created_connections), len(failed_connections))
        
        return {
            "status": "ok",
            "created_connections": created_connections,
            "failed_connections": failed_connections,
            "system_inputs": system_inputs,
            "system_outputs": system_outputs
        }

    # ---------------------------------------------------------------------
    # System I/O validation helper
    def _validate_system_io(
        self,
        saved_inputs: List[str],
        saved_outputs: List[str],
        current_inputs: List[str],
        current_outputs: List[str],
    ) -> Dict[str, Any]:
        """Validate saved system I/O against currently available hardware ports.

        Strategy:
          - If any saved input/output ports are missing from current hardware, we adopt current ports.
          - Otherwise we keep saved ports (even if there are *extra* current ports available).

        Returns a dict describing differences and the resolved ports to use.
        """
        missing_inputs = [p for p in saved_inputs if p not in current_inputs]
        missing_outputs = [p for p in saved_outputs if p not in current_outputs]
        extra_inputs = [p for p in current_inputs if p not in saved_inputs]
        extra_outputs = [p for p in current_outputs if p not in saved_outputs]

        # Decide strategy
        if saved_inputs == [] and saved_outputs == []:
            # Legacy pedalboard without stored system I/O -> adopt current
            strategy = "adopted_current (legacy_missing)"
            resolved_inputs = current_inputs
            resolved_outputs = current_outputs
            changed = True
        elif missing_inputs or missing_outputs:
            # Some saved ports unavailable -> fall back to current hardware set
            strategy = "replaced_missing_with_current"
            resolved_inputs = current_inputs
            resolved_outputs = current_outputs
            changed = True
        else:
            # Keep saved definition (preferred for user intention)
            strategy = "kept_saved"
            resolved_inputs = saved_inputs if saved_inputs else current_inputs
            resolved_outputs = saved_outputs if saved_outputs else current_outputs
            changed = False

        return {
            "saved_inputs": saved_inputs,
            "saved_outputs": saved_outputs,
            "current_inputs": current_inputs,
            "current_outputs": current_outputs,
            "missing_inputs": missing_inputs,
            "missing_outputs": missing_outputs,
            "extra_inputs": extra_inputs,
            "extra_outputs": extra_outputs,
            "strategy": strategy,
            "resolved_inputs": resolved_inputs,
            "resolved_outputs": resolved_outputs,
            "changed": changed,
        }

    # connection helpers
    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)

    def remove_connection(self, connection_id: str) -> bool:
        return self.connections.remove(connection_id)
