"""
Level 2 Tests: Session Manager Direct Calls

These tests call session manager methods directly (simulated via ZMQ for now),
testing the business logic layer.
"""

import pytest
from .test_framework import SessionManagerDirectTestClient


class TestSessionManagerDirect:
    """Direct session manager call tests"""
    
    @pytest.mark.asyncio
    async def test_session_status_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test session status through direct calls"""
        response = await session_manager_direct_client.call("get_session_status")
        assert "success" in response
        
    @pytest.mark.asyncio
    async def test_plugin_management_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test plugin management through session manager"""
        plugin_uri = session_manager_direct_client.get_test_plugin(0)
        
        # Load plugin through session manager
        response = await session_manager_direct_client.call("load_plugin", uri=plugin_uri)
        assert "success" in response
        
        if response.get("success"):
            instance_id = response.get("instance_id")
            
            try:
                # Get plugin list
                list_response = await session_manager_direct_client.call("get_loaded_plugins")
                assert "success" in list_response
                if list_response.get("success"):
                    plugins = list_response.get("plugins", [])
                    assert any(p.get("instance_id") == instance_id for p in plugins)
                    
                # Test parameter update
                param_response = await session_manager_direct_client.call(
                    "update_parameter",
                    instance_id=instance_id,
                    symbol="gain",  # Common parameter
                    value=0.7
                )
                assert "success" in param_response
                
            finally:
                # Remove plugin
                await session_manager_direct_client.call("remove_plugin", instance_id=instance_id)
                
    @pytest.mark.asyncio
    async def test_connection_management_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test audio connection management"""
        plugin_uri_1 = session_manager_direct_client.get_test_plugin(0)
        plugin_uri_2 = session_manager_direct_client.get_test_plugin(1)
        
        # Load two plugins
        response1 = await session_manager_direct_client.call("load_plugin", uri=plugin_uri_1)
        response2 = await session_manager_direct_client.call("load_plugin", uri=plugin_uri_2)
        
        if response1.get("success") and response2.get("success"):
            instance_id_1 = response1.get("instance_id")
            instance_id_2 = response2.get("instance_id")
            
            try:
                # Try to connect plugins (if they have compatible ports)
                connect_response = await session_manager_direct_client.call(
                    "connect_plugins",
                    source_id=instance_id_1,
                    target_id=instance_id_2,
                    source_port=0,
                    target_port=0
                )
                assert "success" in connect_response
                
                # Get connections
                connections_response = await session_manager_direct_client.call("get_connections")
                assert "success" in connections_response
                
                if connect_response.get("success"):
                    # Disconnect
                    disconnect_response = await session_manager_direct_client.call(
                        "disconnect_plugins",
                        source_id=instance_id_1,
                        target_id=instance_id_2,
                        source_port=0,
                        target_port=0
                    )
                    assert "success" in disconnect_response
                    
            finally:
                # Cleanup
                await session_manager_direct_client.call("remove_plugin", instance_id=instance_id_1)
                await session_manager_direct_client.call("remove_plugin", instance_id=instance_id_2)
                
    @pytest.mark.asyncio
    async def test_snapshot_management_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test snapshot management through session manager"""
        # Save current state as snapshot
        snapshot_name = "test_snapshot_direct"
        save_response = await session_manager_direct_client.call("save_snapshot", name=snapshot_name)
        assert "success" in save_response
        
        if save_response.get("success"):
            try:
                # List snapshots
                list_response = await session_manager_direct_client.call("list_snapshots")
                assert "success" in list_response
                if list_response.get("success"):
                    snapshots = list_response.get("snapshots", [])
                    assert any(s.get("name") == snapshot_name for s in snapshots)
                    
                # Load snapshot
                load_response = await session_manager_direct_client.call("load_snapshot", name=snapshot_name)
                assert "success" in load_response
                
            finally:
                # Cleanup snapshot
                await session_manager_direct_client.call("remove_snapshot", name=snapshot_name)
                
    @pytest.mark.asyncio
    async def test_system_monitoring_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test system monitoring through session manager"""
        # Get system status
        response = await session_manager_direct_client.call("get_system_status")
        assert "success" in response
        
        # Get JACK status
        jack_response = await session_manager_direct_client.call("get_jack_status")
        assert "success" in jack_response
        
        # Get CPU usage
        cpu_response = await session_manager_direct_client.call("get_cpu_usage")
        assert "success" in cpu_response
        
    @pytest.mark.asyncio
    async def test_configuration_management_direct(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test configuration management"""
        # Get current config
        get_response = await session_manager_direct_client.call("get_config")
        assert "success" in get_response
        
        # Set a config value
        set_response = await session_manager_direct_client.call(
            "set_config",
            key="test_setting",
            value="test_value"
        )
        assert "success" in set_response
        
        # Verify config was set
        verify_response = await session_manager_direct_client.call("get_config", key="test_setting")
        if verify_response.get("success"):
            assert verify_response.get("value") == "test_value"
            
    @pytest.mark.asyncio
    async def test_error_handling_session_manager(self, session_manager_direct_client: SessionManagerDirectTestClient):
        """Test error handling in session manager"""
        # Invalid plugin URI
        response = await session_manager_direct_client.call("load_plugin", uri="invalid://plugin.uri")
        assert "success" in response
        assert response["success"] is False
        
        # Invalid instance ID
        response = await session_manager_direct_client.call("remove_plugin", instance_id=99999)
        assert "success" in response
        assert response["success"] is False
        
        # Invalid snapshot name
        response = await session_manager_direct_client.call("load_snapshot", name="nonexistent_snapshot")
        assert "success" in response
        assert response["success"] is False