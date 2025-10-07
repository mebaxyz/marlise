"""
Direct ZeroMQ Service Implementation

Minimal ZeroMQ wrapper without ServiceBus package dependencies.
Provides RPC (REQ/REP) and pub/sub functionality.
"""

import asyncio
import json
import logging
import uuid
import zlib
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)


class ZMQService:
    """
    Direct ZeroMQ service for RPC and pub/sub communication
    """

    def __init__(self, service_name: str, base_port: int = 5555):
        self.service_name = service_name
        self.base_port = base_port
        self.context = zmq.asyncio.Context()
        
        # Sockets
        self.rpc_socket = None  # REP socket for handling incoming RPC calls
        self.pub_socket = None  # PUB socket for publishing events
        self.sub_socket = None  # SUB socket for subscribing to events
        self.req_sockets = {}  # REQ sockets for calling other services
        
        # Handlers
        self._handlers: Dict[str, Callable] = {}
        
        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Assign ports based on service name hash
        self._assign_ports()

    def _assign_ports(self):
        """Assign ports based on service name hash for deterministic allocation"""
        service_hash = zlib.crc32(self.service_name.encode("utf-8")) % 1000
        self.rpc_port = self.base_port + service_hash
        self.pub_port = self.base_port + service_hash + 1000
        self.sub_port = self.base_port + service_hash + 2000
        
        logger.info(
            "Service '%s' ports: RPC=%s, PUB=%s, SUB=%s",
            self.service_name, self.rpc_port, self.pub_port, self.sub_port
        )

    async def start(self) -> bool:
        """Start the ZeroMQ service"""
        try:
            # RPC socket (REP) - handles incoming method calls
            self.rpc_socket = self.context.socket(zmq.REP)
            self.rpc_socket.bind(f"tcp://127.0.0.1:{self.rpc_port}")
            
            # PUB socket - publishes events
            self.pub_socket = self.context.socket(zmq.PUB)
            self.pub_socket.bind(f"tcp://127.0.0.1:{self.pub_port}")
            
            # SUB socket - subscribes to events from other services
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            
            # Connect to other services' PUB sockets (simple discovery)
            for offset in range(0, 1000):
                pub_port = self.base_port + offset + 1000
                if pub_port != self.pub_port:
                    try:
                        self.sub_socket.connect(f"tcp://127.0.0.1:{pub_port}")
                    except Exception:
                        pass
            
            self._running = True
            self._tasks.append(asyncio.create_task(self._handle_rpc_calls()))
            
            # Give sockets time to bind
            await asyncio.sleep(0.1)
            
            logger.info("ZMQ Service '%s' started successfully", self.service_name)
            return True
            
        except Exception as e:
            logger.error("Failed to start ZMQ service '%s': %s", self.service_name, e)
            await self.stop()
            return False

    async def stop(self):
        """Stop the ZeroMQ service"""
        self._running = False
        
        # Cancel tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close sockets
        if self.rpc_socket:
            self.rpc_socket.close()
        if self.pub_socket:
            self.pub_socket.close()
        if self.sub_socket:
            self.sub_socket.close()
        
        for socket in self.req_sockets.values():
            socket.close()
        self.req_sockets.clear()
        
        # Terminate context
        self.context.term()
        
        logger.info("ZMQ Service '%s' stopped", self.service_name)

    def register_handler(self, method_name: str, handler: Callable) -> "ZMQService":
        """Register a handler for RPC method calls"""
        self._handlers[method_name] = handler
        logger.debug("Registered handler for method '%s'", method_name)
        return self

    async def publish_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish an event to all subscribers"""
        if not self.pub_socket or not self._running:
            return False
        
        try:
            message = {
                "event_type": event_type,
                "data": data,
                "source_service": self.service_name,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Send as multipart message: [topic, data]
            await self.pub_socket.send_multipart([
                event_type.encode("utf-8"),
                json.dumps(message).encode("utf-8")
            ])
            
            logger.debug("Published event '%s' from '%s'", event_type, self.service_name)
            return True
            
        except Exception as e:
            logger.error("Failed to publish event '%s': %s", event_type, e)
            return False

    async def call(self, service_name: str, method: str, timeout: Optional[float] = None, **kwargs) -> Any:
        """Call a method on another service"""
        try:
            # Get or create REQ socket for this service
            if service_name not in self.req_sockets:
                service_port = self._get_service_rpc_port(service_name)
                req_socket = self.context.socket(zmq.REQ)
                req_socket.connect(f"tcp://127.0.0.1:{service_port}")
                self.req_sockets[service_name] = req_socket
            
            req_socket = self.req_sockets[service_name]
            
            # Create request
            request_data = {
                "method": method,
                "params": kwargs,
                "source_service": self.service_name,
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
            }
            
            # Send request and wait for response
            await req_socket.send_json(request_data)
            
            if timeout is not None:
                response_data = await asyncio.wait_for(req_socket.recv_json(), timeout=timeout)
            else:
                response_data = await req_socket.recv_json()
            
            if response_data.get("error"):
                raise RuntimeError(f"Remote service error: {response_data['error']}")
            
            return response_data.get("result")
            
        except Exception as e:
            logger.error("Failed to call %s.%s: %s", service_name, method, e)
            raise

    def _get_service_rpc_port(self, service_name: str) -> int:
        """Get the RPC port for a service"""
        service_hash = zlib.crc32(service_name.encode("utf-8")) % 1000
        return self.base_port + service_hash

    async def _handle_rpc_calls(self):
        """Background task to handle incoming RPC calls"""
        logger.info("Starting RPC handler for service '%s'", self.service_name)
        
        while self._running:
            try:
                if not self.rpc_socket:
                    await asyncio.sleep(0.1)
                    continue
                
                # Receive request with timeout
                try:
                    request_data = await asyncio.wait_for(
                        self.rpc_socket.recv_json(zmq.NOBLOCK), timeout=0.1
                    )
                except (asyncio.TimeoutError, zmq.Again):
                    await asyncio.sleep(0.01)
                    continue
                
                method = request_data.get("method")
                params = request_data.get("params", {})
                request_id = request_data.get("request_id")
                
                logger.debug("Received RPC call: %s", method)
                
                # Handle the request
                if method in self._handlers:
                    try:
                        # Call handler
                        if asyncio.iscoroutinefunction(self._handlers[method]):
                            result = await self._handlers[method](**params)
                        else:
                            result = self._handlers[method](**params)
                        
                        # Send response
                        response = {
                            "request_id": request_id,
                            "result": result,
                            "timestamp": datetime.now().isoformat(),
                        }
                        await self.rpc_socket.send_json(response)
                        
                    except Exception as e:
                        logger.error("Handler error for %s: %s", method, e)
                        # Send error response
                        response = {
                            "request_id": request_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                        await self.rpc_socket.send_json(response)
                else:
                    # Method not found
                    response = {
                        "request_id": request_id,
                        "error": f"Method '{method}' not found",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await self.rpc_socket.send_json(response)
                    
            except Exception as e:
                logger.error("RPC handler error: %s", e)
                await asyncio.sleep(0.1)
        
        logger.info("RPC handler stopped for service '%s'", self.service_name)

    def is_running(self) -> bool:
        """Check if the service is running"""
        return self._running