"""
Pedalboard management ZMQ handlers
"""
import logging
from typing import Any, Dict

from .decorators import zmq_handler

logger = logging.getLogger(__name__)


class PedalboardHandlers:
    """Pedalboard management ZMQ RPC method handlers"""

    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service

    def register_handlers(self):
        """Register all pedalboard management handlers using decorator discovery"""
        # Handlers are registered via @zmq_handler decorator by the parent class
        pass

    # Pedalboard management handlers
    @zmq_handler("reset_pedalboard")
    async def handle_reset_pedalboard(self, **_kwargs) -> Dict[str, Any]:
        """Reset pedalboard to empty state"""
        try:
            await self.session_manager.reset_session()
            return {"success": True}
        except Exception as e:
            logger.error("Failed to reset pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("save_pedalboard")
    async def handle_save_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Save current pedalboard"""
        try:
            # Use existing session manager save_pedalboard method
            result = await self.session_manager.save_pedalboard()
            return {"success": True, "pedalboard": result["pedalboard"], "saved_id": result["saved_id"]}
        except Exception as e:
            logger.error("Failed to save pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_pedalboard")
    async def handle_load_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Load pedalboard by ID or name"""
        try:
            from ..infrastructure.storage import load_pedalboard, list_pedalboards
            
            pb_id = kwargs.get("id")
            name = kwargs.get("name")
            
            if not pb_id and not name:
                return {"success": False, "error": "Missing 'id' or 'name' parameter"}
            
            # If name provided, find ID by listing pedalboards
            if name and not pb_id:
                pedalboards = list_pedalboards()
                for pb in pedalboards:
                    if pb.get("name") == name:
                        pb_id = pb["id"]
                        break
                if not pb_id:
                    return {"success": False, "error": f"Pedalboard '{name}' not found"}
            
            # Load pedalboard data from storage
            if not pb_id:
                return {"success": False, "error": "Could not resolve pedalboard ID"}
            
            pedalboard_data = load_pedalboard(pb_id)
            if not pedalboard_data:
                return {"success": False, "error": f"Pedalboard '{pb_id}' not found"}
            
            # Use existing session manager load_pedalboard method
            result = await self.session_manager.load_pedalboard(pedalboard_data)
            return {"success": True, "pedalboard": result["pedalboard"], "plugins_loaded": result["plugins_loaded"]}
        except Exception as e:
            logger.error("Failed to load pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_current_pedalboard")
    async def handle_get_current_pedalboard(self, **_kwargs) -> Dict[str, Any]:
        """Get current pedalboard state"""
        try:
            result = await self.session_manager.get_current_pedalboard()
            return {"success": True, "pedalboard": result["pedalboard"]}
        except Exception as e:
            logger.error("Failed to get current pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_pedalboard_list")
    async def handle_get_pedalboard_list(self, **_kwargs) -> Dict[str, Any]:
        """Get list of available pedalboards"""
        try:
            from ..infrastructure.storage import list_pedalboards
            
            pedalboards = list_pedalboards()
            return {"success": True, "pedalboards": pedalboards}
        except Exception as e:
            logger.error("Failed to get pedalboard list: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("delete_pedalboard")
    async def handle_delete_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Delete pedalboard by ID or name"""
        try:
            from ..infrastructure.storage import delete_pedalboard, list_pedalboards
            
            pb_id = kwargs.get("id")
            name = kwargs.get("name")
            
            if not pb_id and not name:
                return {"success": False, "error": "Missing 'id' or 'name' parameter"}
            
            # If name provided, find ID by listing pedalboards
            if name and not pb_id:
                pedalboards = list_pedalboards()
                for pb in pedalboards:
                    if pb.get("name") == name:
                        pb_id = pb["id"]
                        break
                if not pb_id:
                    return {"success": False, "error": f"Pedalboard '{name}' not found"}
            
            if not pb_id:
                return {"success": False, "error": "Could not resolve pedalboard ID"}
                
            success = delete_pedalboard(pb_id)
            if success:
                return {"success": True, "deleted_id": pb_id}
            else:
                return {"success": False, "error": f"Pedalboard '{pb_id}' not found"}
        except Exception as e:
            logger.error("Failed to delete pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("rename_pedalboard")
    async def handle_rename_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Rename pedalboard"""
        try:
            old_name = kwargs.get("old_name")
            new_name = kwargs.get("new_name")

            if not old_name or not new_name:
                return {"success": False, "error": "Missing 'old_name' or 'new_name' parameter"}

            # Use session manager to handle rename operation
            result = await self.session_manager.rename_pedalboard(old_name, new_name)
            return result
        except Exception as e:
            logger.error("Failed to rename pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("create_pedalboard")
    async def handle_create_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Create new pedalboard"""
        try:
            name = kwargs.get("name")
            description = kwargs.get("description", "")
            if not name:
                return {"success": False, "error": "Missing 'name' parameter"}

            result = await self.session_manager.create_pedalboard(name, description)
            return {"success": True, "pedalboard_id": result["pedalboard_id"], "pedalboard": result["pedalboard"]}
        except Exception as e:
            logger.error("Failed to create pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("duplicate_pedalboard")
    async def handle_duplicate_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Duplicate pedalboard"""
        try:
            name = kwargs.get("name")
            new_name = kwargs.get("new_name")

            if not name or not new_name:
                return {"success": False, "error": "Missing 'name' or 'new_name' parameter"}

            # Use session manager to handle duplicate operation
            result = await self.session_manager.duplicate_pedalboard(name, new_name)
            return result
        except Exception as e:
            logger.error("Failed to duplicate pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("export_pedalboard")
    async def handle_export_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Export pedalboard to file"""
        try:
            from ..infrastructure.storage import export_pedalboard, list_pedalboards
            
            pb_id = kwargs.get("id")
            name = kwargs.get("name")
            filename = kwargs.get("filename")

            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}
            
            if not pb_id and not name:
                return {"success": False, "error": "Missing 'id' or 'name' parameter"}

            # If name provided, find ID by listing pedalboards
            if name and not pb_id:
                pedalboards = list_pedalboards()
                for pb in pedalboards:
                    if pb.get("name") == name:
                        pb_id = pb["id"]
                        break
                if not pb_id:
                    return {"success": False, "error": f"Pedalboard '{name}' not found"}
            
            if not pb_id:
                return {"success": False, "error": "Could not resolve pedalboard ID"}
                
            success = export_pedalboard(pb_id, filename)
            if success:
                return {"success": True, "exported_file": filename}
            else:
                return {"success": False, "error": f"Failed to export pedalboard '{pb_id}'"}
        except Exception as e:
            logger.error("Failed to export pedalboard: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("import_pedalboard")
    async def handle_import_pedalboard(self, **kwargs) -> Dict[str, Any]:
        """Import pedalboard from file"""
        try:
            from ..infrastructure.storage import import_pedalboard
            
            filename = kwargs.get("filename")
            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}

            result = import_pedalboard(filename)
            if result:
                pb_id, path = result
                return {"success": True, "imported_id": pb_id, "imported_path": path}
            else:
                return {"success": False, "error": f"Failed to import pedalboard from '{filename}'"}
        except Exception as e:
            logger.error("Failed to import pedalboard: %s", e)
            return {"success": False, "error": str(e)}