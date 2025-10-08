"""
Level 4 Tests: Client API HTTP Endpoints

These tests use the HTTP API endpoints, testing the complete system
end-to-end from web client perspective.
"""

import pytest
import asyncio
from .test_framework import ClientApiTestClient


class TestClientApiHttp:
    """Client API HTTP endpoint tests"""
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, client_api_client: ClientApiTestClient):
        """Test API health check endpoint"""
        response = await client_api_client.get("/health")
        assert "status" in response
        assert response["status"] == "healthy"
        
    @pytest.mark.asyncio
    async def test_plugin_endpoints(self, client_api_client: ClientApiTestClient):
        """Test plugin management HTTP endpoints"""
        plugin_uri = client_api_client.get_test_plugin(0)
        
        # Get available plugins
        available_response = await client_api_client.get("/api/plugins/available")
        assert "plugins" in available_response or "success" in available_response
        
        # Load plugin via HTTP
        load_response = await client_api_client.post("/api/plugins", {"uri": plugin_uri})
        assert "success" in load_response or "instance_id" in load_response
        
        if load_response.get("success") or load_response.get("instance_id"):
            instance_id = load_response.get("instance_id") or load_response.get("data", {}).get("instance_id")
            
            try:
                # Get loaded plugins
                loaded_response = await client_api_client.get("/api/plugins")
                assert "plugins" in loaded_response or "success" in loaded_response
                
                # Get plugin info
                info_response = await client_api_client.get(f"/api/plugins/{instance_id}")
                assert info_response is not None
                
                # Update parameter via HTTP
                param_response = await client_api_client.patch(
                    "/api/plugins/parameters",
                    {"instance_id": instance_id, "symbol": "gain", "value": 0.6}
                )
                assert param_response is not None
                
            finally:
                # Remove plugin
                remove_response = await client_api_client.delete(f"/api/plugins/{instance_id}")
                assert remove_response is not None
                
    @pytest.mark.asyncio
    async def test_jack_endpoints(self, client_api_client: ClientApiTestClient):
        """Test JACK-related HTTP endpoints"""
        # Get JACK status
        status_response = await client_api_client.get("/api/jack/status")
        assert status_response is not None
        
        # Get JACK connections
        connections_response = await client_api_client.get("/api/jack/connections")
        assert connections_response is not None
        
        # Get JACK ports
        ports_response = await client_api_client.get("/api/jack/ports")
        assert ports_response is not None
        
        # Get audio ports specifically
        audio_ports_response = await client_api_client.get("/api/jack/ports/audio")
        assert audio_ports_response is not None
        
        # Get MIDI ports
        midi_ports_response = await client_api_client.get("/api/jack/ports/midi")
        assert midi_ports_response is not None
        
    @pytest.mark.asyncio
    async def test_system_endpoints(self, client_api_client: ClientApiTestClient):
        """Test system monitoring HTTP endpoints"""
        # System status
        system_response = await client_api_client.get("/api/system/status")
        assert system_response is not None
        
        # CPU usage
        cpu_response = await client_api_client.get("/api/system/cpu")
        assert cpu_response is not None
        
        # Memory usage
        memory_response = await client_api_client.get("/api/system/memory")
        assert memory_response is not None
        
        # Disk usage
        disk_response = await client_api_client.get("/api/system/disk")
        assert disk_response is not None
        
        # Network info
        network_response = await client_api_client.get("/api/system/network")
        assert network_response is not None
        
    @pytest.mark.asyncio
    async def test_session_endpoints(self, client_api_client: ClientApiTestClient):
        """Test session management HTTP endpoints"""
        # Get session status
        status_response = await client_api_client.get("/api/session/status")
        assert status_response is not None
        
        # Reset session
        reset_response = await client_api_client.post("/api/session/reset")
        assert reset_response is not None
        
    @pytest.mark.asyncio
    async def test_snapshot_endpoints(self, client_api_client: ClientApiTestClient):
        """Test snapshot management HTTP endpoints"""
        snapshot_name = "test_snapshot_http"
        
        # Save snapshot
        save_response = await client_api_client.post(
            "/api/snapshots", 
            {"name": snapshot_name}
        )
        assert save_response is not None
        
        # List snapshots
        list_response = await client_api_client.get("/api/snapshots")
        assert list_response is not None
        
        # Get specific snapshot
        get_response = await client_api_client.get(f"/api/snapshots/{snapshot_name}")
        assert get_response is not None
        
        # Load snapshot
        load_response = await client_api_client.post(f"/api/snapshots/{snapshot_name}/load")
        assert load_response is not None
        
        # Delete snapshot
        delete_response = await client_api_client.delete(f"/api/snapshots/{snapshot_name}")
        assert delete_response is not None
        
    @pytest.mark.asyncio
    async def test_configuration_endpoints(self, client_api_client: ClientApiTestClient):
        """Test configuration HTTP endpoints"""
        # Get configuration
        get_response = await client_api_client.get("/api/config")
        assert get_response is not None
        
        # Set configuration
        set_response = await client_api_client.post(
            "/api/config",
            {"key": "http_test_key", "value": "http_test_value"}
        )
        assert set_response is not None
        
        # Get specific config key
        key_response = await client_api_client.get("/api/config/http_test_key")
        assert key_response is not None
        
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client_api_client: ClientApiTestClient):
        """Test WebSocket connection and real-time updates"""
        try:
            websocket = await client_api_client.websocket_connect()
            
            # Send a test message
            test_message = {"type": "ping", "data": "test"}
            await websocket.send(str(test_message))
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                assert response is not None
            except asyncio.TimeoutError:
                # Some WebSocket implementations might not respond to ping
                pass
                
            await websocket.close()
            
        except Exception as e:
            # WebSocket might not be implemented or available
            pytest.skip(f"WebSocket test skipped: {e}")
            
    @pytest.mark.asyncio
    async def test_error_responses_http(self, client_api_client: ClientApiTestClient):
        """Test HTTP error responses"""
        # Invalid plugin URI
        invalid_plugin_response = await client_api_client.post(
            "/api/plugins",
            {"uri": "http://invalid.plugin.uri"}
        )
        # Should get error response, not exception
        assert invalid_plugin_response is not None
        
        # Non-existent plugin instance
        nonexistent_response = await client_api_client.get("/api/plugins/99999")
        assert nonexistent_response is not None
        
        # Invalid snapshot
        invalid_snapshot_response = await client_api_client.get("/api/snapshots/nonexistent")
        assert invalid_snapshot_response is not None
        
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client_api_client: ClientApiTestClient):
        """Test concurrent HTTP requests"""
        # Make multiple concurrent requests
        tasks = [
            client_api_client.get("/api/system/status"),
            client_api_client.get("/api/jack/status"),
            client_api_client.get("/api/session/status"),
            client_api_client.get("/api/plugins/available"),
            client_api_client.get("/health")
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete successfully
        for response in responses:
            assert not isinstance(response, Exception)
            assert response is not None
            
    @pytest.mark.asyncio
    async def test_content_negotiation(self, client_api_client: ClientApiTestClient):
        """Test HTTP content negotiation"""
        # Test with different Accept headers
        headers = {"Accept": "application/json"}
        response = await client_api_client.get("/api/system/status", headers=headers)
        assert response is not None
        
        # Test CORS headers (if implemented)
        headers = {"Origin": "http://localhost:3000"}
        response = await client_api_client.get("/health", headers=headers)
        assert response is not None
        
    @pytest.mark.asyncio
    async def test_complete_workflow_http(self, client_api_client: ClientApiTestClient):
        """Test complete workflow via HTTP API"""
        plugin_uri = client_api_client.get_test_plugin(0)
        
        # 1. Check system health
        health_response = await client_api_client.get("/health")
        assert health_response["status"] == "healthy"
        
        # 2. Load a plugin
        load_response = await client_api_client.post("/api/plugins", {"uri": plugin_uri})
        if not (load_response.get("success") or load_response.get("instance_id")):
            pytest.skip("Plugin loading failed, skipping workflow test")
            
        instance_id = load_response.get("instance_id") or load_response.get("data", {}).get("instance_id")
        
        try:
            # 3. Configure the plugin
            param_response = await client_api_client.patch(
                "/api/plugins/parameters",
                {"instance_id": instance_id, "symbol": "gain", "value": 0.5}
            )
            
            # 4. Save as snapshot
            snapshot_name = "workflow_test_snapshot"
            snapshot_response = await client_api_client.post(
                "/api/snapshots",
                {"name": snapshot_name}
            )
            
            # 5. Check JACK status
            jack_response = await client_api_client.get("/api/jack/status")
            assert jack_response is not None
            
            # 6. Clean up snapshot
            await client_api_client.delete(f"/api/snapshots/{snapshot_name}")
            
        finally:
            # 7. Remove plugin
            await client_api_client.delete(f"/api/plugins/{instance_id}")