"""
Level 1 Tests: Mod-Host Bridge Direct Communication

These tests directly communicate with the modhost-bridge component via ZeroMQ,
testing the lowest level of the audio engine stack.
"""

import pytest
from .test_framework import ModHostBridgeTestClient


class TestModHostBridgeDirect:
    """Direct mod-host bridge communication tests"""
    
    @pytest.mark.asyncio
    async def test_bridge_connection(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test basic connection to modhost-bridge"""
        # Try a simple ping-like command
        response = await modhost_bridge_client.call("get_status")
        assert response is not None
        
    @pytest.mark.asyncio
    async def test_plugin_loading_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test plugin loading through bridge"""
        plugin_uri = modhost_bridge_client.get_test_plugin(0)
        
        # Load plugin
        response = await modhost_bridge_client.call("load_plugin", uri=plugin_uri)
        assert "success" in response
        
        if response.get("success"):
            instance_id = response.get("instance_id")
            assert instance_id is not None
            
            # Remove plugin
            cleanup_response = await modhost_bridge_client.call("remove_plugin", instance_id=instance_id)
            assert "success" in cleanup_response
            
    @pytest.mark.asyncio
    async def test_parameter_control_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test parameter control through bridge"""
        plugin_uri = modhost_bridge_client.get_test_plugin(0)
        
        # Load plugin first
        load_response = await modhost_bridge_client.call("load_plugin", uri=plugin_uri)
        if not load_response.get("success"):
            pytest.skip("Plugin loading failed, skipping parameter test")
            
        instance_id = load_response.get("instance_id")
        
        try:
            # Get plugin info to find parameters
            info_response = await modhost_bridge_client.call("get_plugin_info", instance_id=instance_id)
            
            if info_response.get("success") and info_response.get("parameters"):
                # Test setting a parameter
                param = info_response["parameters"][0]
                param_symbol = param.get("symbol")
                
                if param_symbol:
                    param_response = await modhost_bridge_client.call(
                        "set_parameter", 
                        instance_id=instance_id,
                        symbol=param_symbol,
                        value=0.5
                    )
                    assert "success" in param_response
                    
        finally:
            # Cleanup
            await modhost_bridge_client.call("remove_plugin", instance_id=instance_id)
            
    @pytest.mark.asyncio
    async def test_jack_status_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test JACK status through bridge"""
        response = await modhost_bridge_client.call("get_jack_status")
        assert "success" in response
        
        if response.get("success"):
            status = response.get("status")
            assert status is not None
            # Should have basic JACK info
            assert "sample_rate" in status or "samplerate" in status
            
    @pytest.mark.asyncio
    async def test_jack_ports_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test JACK port listing through bridge"""
        response = await modhost_bridge_client.call("get_jack_ports")
        assert "success" in response
        
        if response.get("success"):
            ports = response.get("ports", [])
            # Should have some system ports from dummy backend
            assert isinstance(ports, list)
            
    @pytest.mark.asyncio
    async def test_multiple_plugins_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test loading multiple plugins through bridge"""
        plugin_uri_1 = modhost_bridge_client.get_test_plugin(0)
        plugin_uri_2 = modhost_bridge_client.get_test_plugin(1)
        
        # Load first plugin
        response1 = await modhost_bridge_client.call("load_plugin", uri=plugin_uri_1)
        if not response1.get("success"):
            pytest.skip("First plugin loading failed")
            
        # Load second plugin
        response2 = await modhost_bridge_client.call("load_plugin", uri=plugin_uri_2)
        if not response2.get("success"):
            # Cleanup first plugin
            await modhost_bridge_client.call("remove_plugin", instance_id=response1.get("instance_id"))
            pytest.skip("Second plugin loading failed")
            
        try:
            # Both should have different instance IDs
            instance_id_1 = response1.get("instance_id")
            instance_id_2 = response2.get("instance_id")
            
            assert instance_id_1 != instance_id_2
            assert instance_id_1 is not None
            assert instance_id_2 is not None
            
        finally:
            # Cleanup both plugins
            await modhost_bridge_client.call("remove_plugin", instance_id=response1.get("instance_id"))
            await modhost_bridge_client.call("remove_plugin", instance_id=response2.get("instance_id"))
            
    @pytest.mark.asyncio
    async def test_error_handling_direct(self, modhost_bridge_client: ModHostBridgeTestClient):
        """Test error handling in bridge"""
        # Try to load non-existent plugin
        response = await modhost_bridge_client.call("load_plugin", uri="http://invalid.plugin.uri")
        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        
        # Try to remove non-existent plugin
        response = await modhost_bridge_client.call("remove_plugin", instance_id=99999)
        assert "success" in response
        assert response["success"] is False
        
        # Try to set parameter on non-existent plugin
        response = await modhost_bridge_client.call(
            "set_parameter", 
            instance_id=99999,
            symbol="gain",
            value=0.5
        )
        assert "success" in response
        assert response["success"] is False