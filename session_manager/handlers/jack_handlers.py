"""
JACK audio system ZMQ handlers
"""
import logging
from typing import Any, Dict

from .decorators import zmq_handler

logger = logging.getLogger(__name__)


class JackHandlers:
    """JACK audio system ZMQ RPC method handlers"""

    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service

    def register_handlers(self):
        """Register all JACK audio system handlers using decorator discovery"""
        # Handlers are registered via @zmq_handler decorator by the parent class
        pass

    # JACK audio system handlers
    @zmq_handler("get_jack_status")
    async def handle_get_jack_status(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK server status"""
        try:
            # Forward to bridge client for JACK status
            result = await self.bridge_client.call("get_jack_status")
            return result
        except Exception as e:
            logger.error("Failed to get JACK status: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_connections")
    async def handle_get_jack_connections(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK port connections"""
        try:
            # Forward to bridge client for JACK connections
            result = await self.bridge_client.call("get_jack_connections")
            return result
        except Exception as e:
            logger.error("Failed to get JACK connections: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("connect_jack_ports")
    async def handle_connect_jack_ports(self, **kwargs) -> Dict[str, Any]:
        """Connect JACK ports"""
        try:
            port1 = kwargs.get("port1")
            port2 = kwargs.get("port2")

            if not port1 or not port2:
                return {"success": False, "error": "Missing 'port1' or 'port2' parameter"}

            # Forward to bridge client for JACK port connection
            result = await self.bridge_client.call("connect_jack_ports", port1=port1, port2=port2)
            return result
        except Exception as e:
            logger.error("Failed to connect JACK ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("disconnect_jack_ports")
    async def handle_disconnect_jack_ports(self, **kwargs) -> Dict[str, Any]:
        """Disconnect JACK ports"""
        try:
            port1 = kwargs.get("port1")
            port2 = kwargs.get("port2")

            if not port1 or not port2:
                return {"success": False, "error": "Missing 'port1' or 'port2' parameter"}

            # Forward to bridge client for JACK port disconnection
            result = await self.bridge_client.call("disconnect_jack_ports", port1=port1, port2=port2)
            return result
        except Exception as e:
            logger.error("Failed to disconnect JACK ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_ports")
    async def handle_get_jack_ports(self, **_kwargs) -> Dict[str, Any]:
        """Get all JACK ports"""
        try:
            # Forward to bridge client for JACK ports
            result = await self.bridge_client.call("get_jack_ports")
            return result
        except Exception as e:
            logger.error("Failed to get JACK ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_audio_ports")
    async def handle_get_jack_audio_ports(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK audio ports"""
        try:
            # Forward to bridge client for JACK audio ports
            result = await self.bridge_client.call("get_jack_audio_ports")
            return result
        except Exception as e:
            logger.error("Failed to get JACK audio ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_midi_ports")
    async def handle_get_jack_midi_ports(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK MIDI ports"""
        try:
            # Forward to bridge client for JACK MIDI ports
            result = await self.bridge_client.call("get_jack_midi_ports")
            return result
        except Exception as e:
            logger.error("Failed to get JACK MIDI ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_cv_ports")
    async def handle_get_jack_cv_ports(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK CV ports"""
        try:
            # Forward to bridge client for JACK CV ports
            result = await self.bridge_client.call("get_jack_cv_ports")
            return result
        except Exception as e:
            logger.error("Failed to get JACK CV ports: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_transport")
    async def handle_set_jack_transport(self, **kwargs) -> Dict[str, Any]:
        """Set JACK transport state"""
        try:
            state = kwargs.get("state")
            if state is None:
                return {"success": False, "error": "Missing 'state' parameter"}

            # Forward to bridge client for JACK transport control
            result = await self.bridge_client.call("set_jack_transport", state=state)
            return result
        except Exception as e:
            logger.error("Failed to set JACK transport: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_transport")
    async def handle_get_jack_transport(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK transport state"""
        try:
            # Forward to bridge client for JACK transport state
            result = await self.bridge_client.call("get_jack_transport")
            return result
        except Exception as e:
            logger.error("Failed to get JACK transport: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_samplerate")
    async def handle_get_jack_samplerate(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK sample rate"""
        try:
            # Forward to bridge client for JACK sample rate
            result = await self.bridge_client.call("get_jack_samplerate")
            return result
        except Exception as e:
            logger.error("Failed to get JACK samplerate: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_buffersize")
    async def handle_get_jack_buffersize(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK buffer size"""
        try:
            # Forward to bridge client for JACK buffer size
            result = await self.bridge_client.call("get_jack_buffersize")
            return result
        except Exception as e:
            logger.error("Failed to get JACK buffersize: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_buffersize")
    async def handle_set_jack_buffersize(self, **kwargs) -> Dict[str, Any]:
        """Set JACK buffer size"""
        try:
            buffersize = kwargs.get("buffersize")
            if buffersize is None:
                return {"success": False, "error": "Missing 'buffersize' parameter"}

            # Forward to bridge client for JACK buffer size control
            result = await self.bridge_client.call("set_jack_buffersize", buffersize=buffersize)
            return result
        except Exception as e:
            logger.error("Failed to set JACK buffersize: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_latency")
    async def handle_get_jack_latency(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK latency"""
        try:
            # Forward to bridge client for JACK latency information
            result = await self.bridge_client.call("get_jack_latency")
            return result
        except Exception as e:
            logger.error("Failed to get JACK latency: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_xruns")
    async def handle_get_jack_xruns(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK xruns count"""
        try:
            # Forward to bridge client for JACK xrun information
            result = await self.bridge_client.call("get_jack_xruns")
            return result
        except Exception as e:
            logger.error("Failed to get JACK xruns: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("reset_jack_xruns")
    async def handle_reset_jack_xruns(self, **_kwargs) -> Dict[str, Any]:
        """Reset JACK xruns counter"""
        try:
            # Forward to bridge client for JACK xrun reset
            result = await self.bridge_client.call("reset_jack_xruns")
            return result
        except Exception as e:
            logger.error("Failed to reset JACK xruns: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_dsp_load")
    async def handle_get_jack_dsp_load(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK DSP load"""
        try:
            # Forward to bridge client for JACK DSP load
            result = await self.bridge_client.call("get_jack_dsp_load")
            return result
        except Exception as e:
            logger.error("Failed to get JACK DSP load: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_freewheel")
    async def handle_get_jack_freewheel(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK freewheel state"""
        try:
            # Forward to bridge client for JACK freewheel state
            result = await self.bridge_client.call("get_jack_freewheel")
            return result
        except Exception as e:
            logger.error("Failed to get JACK freewheel: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_freewheel")
    async def handle_set_jack_freewheel(self, **kwargs) -> Dict[str, Any]:
        """Set JACK freewheel state"""
        try:
            enabled = kwargs.get("enabled")
            if enabled is None:
                return {"success": False, "error": "Missing 'enabled' parameter"}

            # Forward to bridge client for JACK freewheel control
            result = await self.bridge_client.call("set_jack_freewheel", enabled=enabled)
            return result
        except Exception as e:
            logger.error("Failed to set JACK freewheel: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_timebase")
    async def handle_get_jack_timebase(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK timebase state"""
        try:
            # Forward to bridge client for JACK timebase
            result = await self.bridge_client.call("get_jack_timebase")
            return result
        except Exception as e:
            logger.error("Failed to get JACK timebase: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_timebase")
    async def handle_set_jack_timebase(self, **kwargs) -> Dict[str, Any]:
        """Set JACK timebase state"""
        try:
            enabled = kwargs.get("enabled")
            if enabled is None:
                return {"success": False, "error": "Missing 'enabled' parameter"}

            # Forward to bridge client for JACK timebase control
            result = await self.bridge_client.call("set_jack_timebase", enabled=enabled)
            return result
        except Exception as e:
            logger.error("Failed to set JACK timebase: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_repl_sync")
    async def handle_get_jack_repl_sync(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK repl sync state"""
        try:
            # Forward to bridge client for JACK repl sync state
            result = await self.bridge_client.call("get_jack_repl_sync")
            return result
        except Exception as e:
            logger.error("Failed to get JACK repl sync: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_repl_sync")
    async def handle_set_jack_repl_sync(self, **kwargs) -> Dict[str, Any]:
        """Set JACK repl sync state"""
        try:
            enabled = kwargs.get("enabled")
            if enabled is None:
                return {"success": False, "error": "Missing 'enabled' parameter"}

            # Forward to bridge client for JACK repl sync control
            result = await self.bridge_client.call("set_jack_repl_sync", enabled=enabled)
            return result
        except Exception as e:
            logger.error("Failed to set JACK repl sync: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_jack_repl_latency")
    async def handle_get_jack_repl_latency(self, **_kwargs) -> Dict[str, Any]:
        """Get JACK repl latency"""
        try:
            # Forward to bridge client for JACK repl latency
            result = await self.bridge_client.call("get_jack_repl_latency")
            return result
        except Exception as e:
            logger.error("Failed to get JACK repl latency: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_jack_repl_latency")
    async def handle_set_jack_repl_latency(self, **kwargs) -> Dict[str, Any]:
        """Set JACK repl latency"""
        try:
            latency = kwargs.get("latency")
            if latency is None:
                return {"success": False, "error": "Missing 'latency' parameter"}

            # Forward to bridge client for JACK repl latency control
            result = await self.bridge_client.call("set_jack_repl_latency", latency=latency)
            return result
        except Exception as e:
            logger.error("Failed to set JACK repl latency: %s", e)
            return {"success": False, "error": str(e)}