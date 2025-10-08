#!/usr/bin/env python3
"""
Mock modhost-bridge service for testing
Simulates the modhost-bridge ZMQ interface
"""

import asyncio
import json
import logging
import signal
import sys
import zmq
import zmq.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockModHostBridge:
    def __init__(self, zmq_port=6000, modhost_port=5555):
        self.zmq_port = zmq_port
        self.modhost_port = modhost_port
        self.context = None
        self.socket = None
        self.running = True
        
    async def connect_to_modhost(self, command):
        """Send command to mock mod-host"""
        try:
            reader, writer = await asyncio.open_connection('localhost', self.modhost_port)
            writer.write((command + "\n").encode())
            await writer.drain()
            
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            
            return response.decode().strip()
        except Exception as e:
            logger.error(f"Failed to connect to mod-host: {e}")
            return "resp -1"
    
    async def handle_request(self, request):
        """Handle ZMQ JSON-RPC requests"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id", 1)
            
            logger.info(f"Processing request: {method}")
            
            if method == "load_plugin":
                uri = params.get("uri", "")
                modhost_cmd = f"add {uri}"
                response = await self.connect_to_modhost(modhost_cmd)
                
                if response.startswith("resp ") and response.split()[1] != "-1":
                    instance_id = int(response.split()[1])
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "success": True,
                            "instance_id": instance_id
                        },
                        "id": request_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0", 
                        "error": {
                            "code": -1,
                            "message": "Failed to load plugin"
                        },
                        "id": request_id
                    }
            
            elif method == "remove_plugin":
                instance_id = params.get("instance_id", "")
                modhost_cmd = f"remove {instance_id}"
                response = await self.connect_to_modhost(modhost_cmd)
                
                success = response.startswith("resp 0")
                return {
                    "jsonrpc": "2.0",
                    "result": {"success": success},
                    "id": request_id
                }
            
            elif method == "set_parameter":
                instance_id = params.get("instance_id", "")
                symbol = params.get("symbol", "")
                value = params.get("value", 0)
                
                modhost_cmd = f"param_set {instance_id} {symbol} {value}"
                response = await self.connect_to_modhost(modhost_cmd)
                
                success = response.startswith("resp 0")
                return {
                    "jsonrpc": "2.0",
                    "result": {"success": success},
                    "id": request_id
                }
            
            elif method == "get_jack_status":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "success": True,
                        "status": {
                            "sample_rate": 48000,
                            "buffer_size": 512,
                            "xruns": 0,
                            "dsp_load": 15.2,
                            "running": True
                        }
                    },
                    "id": request_id
                }
            
            elif method == "get_jack_ports":
                return {
                    "jsonrpc": "2.0", 
                    "result": {
                        "success": True,
                        "ports": [
                            {"name": "system:playback_1", "type": "audio", "direction": "output"},
                            {"name": "system:playback_2", "type": "audio", "direction": "output"},
                            {"name": "system:capture_1", "type": "audio", "direction": "input"},
                            {"name": "system:capture_2", "type": "audio", "direction": "input"}
                        ]
                    },
                    "id": request_id
                }
            
            elif method == "get_jack_connections":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "success": True,
                        "connections": []
                    },
                    "id": request_id
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request.get("id", 1)
            }
    
    async def start(self):
        """Start the ZMQ server"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.zmq_port}")
        
        logger.info(f"Mock modhost-bridge started on ZMQ port {self.zmq_port}")
        
        while self.running:
            try:
                # Wait for request
                message = await self.socket.recv_json()
                logger.debug(f"Received: {message}")
                
                # Process request
                response = await self.handle_request(message)
                
                # Send response
                await self.socket.send_json(response)
                logger.debug(f"Sent: {response}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()

async def main():
    bridge = MockModHostBridge()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        bridge.stop()
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())