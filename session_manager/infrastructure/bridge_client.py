"""
Direct ZeroMQ client for communicating with modhost-bridge C++ service.

This client sends the proper JSON format expected by modhost-bridge:
- Audio commands: {"action": "audio", "method": "method_name", ...params}
- Plugin commands: {"action": "plugin", "method": "method_name", ...params}
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)


class BridgeClient:
    """Direct ZeroMQ client for modhost-bridge C++ service"""

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("MODHOST_BRIDGE_ENDPOINT", "tcp://127.0.0.1:6000")
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self._connected = False
        self._running = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self.service_name = "bridge_client"

    async def start(self):
        """Connect to the modhost-bridge"""
        try:
            self.context = zmq.asyncio.Context()
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(self.endpoint)
            self._connected = True
            self._running = True
            logger.info("Connected to modhost-bridge at %s", self.endpoint)
            
            # Start auto-reconnect task
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._auto_reconnect_loop())
                
        except Exception as e:
            logger.error("Failed to connect to modhost-bridge: %s", e)
            raise

    async def stop(self):
        """Disconnect from the modhost-bridge"""
        self._connected = False
        self._running = False
        
        # Cancel reconnect task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
                
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("Disconnected from modhost-bridge")

    async def call(self, service_name: str, method: str, timeout: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """Call method on modhost-bridge service"""
        if service_name != "modhost_bridge":
            raise ValueError(f"This client only supports 'modhost_bridge' service, got '{service_name}'")

        # Determine action type based on method name
        # Methods that are handled by the audio subsystem in modhost-bridge
        if method in {
            "init_jack",
            "close_jack",
            "get_jack_data",
            "get_jack_buffer_size",
            "set_jack_buffer_size",
            "get_jack_sample_rate",
            "connect_jack_ports",
            "disconnect_jack_ports",
            "get_jack_hardware_ports",
            "connect_jack_midi_output_ports",
            "disconnect_jack_midi_output_ports",
        }:
            action = "audio"
        elif method in {
            "load_plugin",
            "unload_plugin",
            "set_parameter",
            "get_parameter",
            "get_available_plugins",
            "get_plugin_essentials",
        }:
            action = "plugin"
        elif method == "create_connection":
            # Handle connection creation directly
            src = kwargs.get("source_plugin") or kwargs.get("source")
            src_port = kwargs.get("source_port")
            tgt = kwargs.get("target_plugin") or kwargs.get("target")
            tgt_port = kwargs.get("target_port")
            if not src or not tgt or src_port is None or tgt_port is None:
                return {
                    "success": False,
                    "error": "create_connection requires source_plugin, source_port, target_plugin, target_port",
                }
            command = f"connect {src}:{src_port} {tgt}:{tgt_port}"
            return await self._send_request({"command": command})
        elif method == "remove_connection":
            # Handle connection removal
            conn_id = kwargs.get("connection_id")
            if conn_id:
                command = f"disconnect_id {conn_id}"
            else:
                src = kwargs.get("source")
                tgt = kwargs.get("target")
                if not src or not tgt:
                    return {"success": False, "error": "remove_connection requires connection_id or source and target"}
                command = f"disconnect {src} {tgt}"
            return await self._send_request({"command": command})
        elif method == "health_check":
            # Use simple audio method for health check
            action = "audio"
            method = "get_jack_sample_rate"
        else:
            return {"success": False, "error": f"Unknown method '{method}' for modhost_bridge service"}

        # Send standard request
        request = {"action": action, "method": method}
        request.update(kwargs)
        return await self._send_request(request)

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to modhost-bridge and return response"""
        if not self._connected or not self.socket:
            return {"success": False, "error": "Not connected to modhost-bridge"}

        try:
            # Send JSON request
            request_json = json.dumps(request)
            await self.socket.send_string(request_json)

            # Wait for response with timeout
            timeout_seconds = float(os.getenv("MODHOST_BRIDGE_TIMEOUT", "5.0"))
            response_json = await asyncio.wait_for(self.socket.recv_string(), timeout=timeout_seconds)

            # Parse and return response
            return json.loads(response_json)

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for modhost-bridge response")
            return {"success": False, "error": "Bridge timeout"}
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from bridge: %s", e)
            return {"success": False, "error": "Invalid bridge response"}
        except Exception as e:
            logger.error("Error communicating with bridge: %s", e)
            self._connected = False  # Mark as disconnected to trigger reconnect
            return {"success": False, "error": f"Bridge communication error: {e}"}

    async def _auto_reconnect_loop(self):
        """Background task that monitors connection and reconnects if needed"""
        reconnect_delay = float(os.getenv("BRIDGE_RECONNECT_DELAY", "2.0"))
        health_check_interval = float(os.getenv("BRIDGE_HEALTH_CHECK_INTERVAL", "5.0"))
        
        while self._running:
            try:
                if not self._connected:
                    logger.info("Bridge disconnected, attempting reconnect...")
                    try:
                        # Close old socket if exists
                        if self.socket:
                            self.socket.close()
                        
                        # Create new socket
                        self.socket = self.context.socket(zmq.REQ)
                        self.socket.connect(self.endpoint)
                        self._connected = True
                        logger.info("Bridge reconnected successfully")
                        
                    except Exception as e:
                        logger.warning("Reconnect attempt failed: %s (retrying in %.1fs)", e, reconnect_delay)
                        await asyncio.sleep(reconnect_delay)
                        continue
                
                # Wait before next health check
                await asyncio.sleep(health_check_interval)
                
            except asyncio.CancelledError:
                logger.info("Auto-reconnect loop cancelled")
                break
            except Exception as e:
                logger.error("Unexpected error in reconnect loop: %s", e)
                await asyncio.sleep(reconnect_delay)


# Alias removed: ServiceBus compatibility layer no longer used
