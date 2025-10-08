"""
Marlise Integration Test Framework

This module provides the base classes and utilities for testing the Marlise system
at different architectural levels:

1. Mod-Host Bridge Direct
2. Session Manager Direct Call  
3. Session Manager ZMQ Call
4. Client API HTTP Endpoint

Each test level builds on the previous one, ensuring end-to-end functionality.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import pytest
import httpx
import zmq
import zmq.asyncio
import websockets

# Test configuration
TEST_HOST = os.getenv("MARLISE_TEST_HOST", "localhost")
TEST_PORT = int(os.getenv("MARLISE_TEST_PORT", "8080"))

# Known test plugins from our test environment
TEST_PLUGINS = [
    "http://calf.sourceforge.net/plugins/Reverb",
    "http://calf.sourceforge.net/plugins/Delay", 
    "http://calf.sourceforge.net/plugins/Compressor",
    "http://plugin.org.uk/swh-plugins/amp",
    "http://plugin.org.uk/swh-plugins/delay_5s",
]

class MarliseTestClient:
    """Base test client with utilities for all test levels"""
    
    def __init__(self):
        self.test_plugins = TEST_PLUGINS
        self.test_host = TEST_HOST
        self.test_port = TEST_PORT
        
    async def wait_for_service(self, host: str, port: int, timeout: int = 30):
        """Wait for a service to become available"""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            await asyncio.sleep(1)
        return False
        
    def get_test_plugin(self, index: int = 0) -> str:
        """Get a test plugin URI by index"""
        return self.test_plugins[index % len(self.test_plugins)]


class ModHostBridgeTestClient(MarliseTestClient):
    """Direct test client for mod-host bridge (Level 1)"""
    
    def __init__(self):
        super().__init__()
        self.context = None
        self.socket = None
        
    async def connect(self):
        """Connect to modhost-bridge via ZeroMQ"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.test_host}:6000")
        
    async def disconnect(self):
        """Disconnect from modhost-bridge"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
            
    async def call(self, method: str, **params) -> Dict[str, Any]:
        """Make a direct call to modhost-bridge"""
        if not self.socket:
            await self.connect()
            
        request = {
            "method": method,
            "params": params,
            "id": 1
        }
        
        await self.socket.send_json(request)
        response = await self.socket.recv_json()
        return response


class SessionManagerDirectTestClient(MarliseTestClient):
    """Direct test client for session manager (Level 2)"""
    
    def __init__(self):
        super().__init__()
        # This would need to import the session manager directly
        # For now, we'll simulate it via ZMQ calls
        
    async def call(self, method: str, **params) -> Dict[str, Any]:
        """Make a direct call to session manager (simulated via ZMQ)"""
        # In a real implementation, this would import and call the session manager directly
        # For testing purposes, we'll use the ZMQ interface
        client = SessionManagerZmqTestClient()
        await client.connect()
        try:
            return await client.call(method, **params)
        finally:
            await client.disconnect()


class SessionManagerZmqTestClient(MarliseTestClient):
    """ZMQ test client for session manager (Level 3)"""
    
    def __init__(self):
        super().__init__()
        self.context = None
        self.socket = None
        
    async def connect(self):
        """Connect to session manager via ZeroMQ"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.test_host}:5718")
        
    async def disconnect(self):
        """Disconnect from session manager"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
            
    async def call(self, method: str, **params) -> Dict[str, Any]:
        """Make a ZMQ call to session manager"""
        if not self.socket:
            await self.connect()
            
        request = {
            "method": method,
            "params": params,
            "id": 1
        }
        
        await self.socket.send_json(request)
        response = await self.socket.recv_json()
        return response


class ClientApiTestClient(MarliseTestClient):
    """HTTP test client for client API (Level 4)"""
    
    def __init__(self):
        super().__init__()
        self.base_url = f"http://{self.test_host}:{self.test_port}"
        self.client = None
        
    @asynccontextmanager
    async def http_client(self):
        """Context manager for HTTP client"""
        async with httpx.AsyncClient() as client:
            self.client = client
            yield client
            
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request to API"""
        async with self.http_client() as client:
            response = await client.get(f"{self.base_url}{endpoint}", **kwargs)
            return response.json()
            
    async def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request to API"""
        async with self.http_client() as client:
            response = await client.post(f"{self.base_url}{endpoint}", json=data, **kwargs)
            return response.json()
            
    async def patch(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make PATCH request to API"""
        async with self.http_client() as client:
            response = await client.patch(f"{self.base_url}{endpoint}", json=data, **kwargs)
            return response.json()
            
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request to API"""
        async with self.http_client() as client:
            response = await client.delete(f"{self.base_url}{endpoint}", **kwargs)
            return response.json()
            
    async def websocket_connect(self, endpoint: str = "/ws"):
        """Connect to WebSocket endpoint"""
        ws_url = f"ws://{self.test_host}:{self.test_port}{endpoint}"
        return await websockets.connect(ws_url)


# Pytest fixtures for different test levels
@pytest.fixture
async def modhost_bridge_client():
    """Fixture for mod-host bridge testing"""
    client = ModHostBridgeTestClient()
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
async def session_manager_direct_client():
    """Fixture for session manager direct testing"""
    client = SessionManagerDirectTestClient()
    yield client


@pytest.fixture
async def session_manager_zmq_client():
    """Fixture for session manager ZMQ testing"""
    client = SessionManagerZmqTestClient()
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
async def client_api_client():
    """Fixture for client API HTTP testing"""
    client = ClientApiTestClient()
    # Wait for API to be ready
    assert await client.wait_for_service(client.test_host, client.test_port)
    yield client


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()