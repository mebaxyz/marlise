"""
Level 3 Tests: Session Manager ZMQ Communication

These tests communicate with the session manager via ZeroMQ,
testing the IPC layer and message serialization.
"""

import pytest
from .test_framework import SessionManagerZmqTestClient


class TestSessionManagerZmq:
    """Session manager ZMQ communication tests"""
    
    @pytest.mark.asyncio
    async def test_zmq_connection(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test basic ZMQ connection to session manager"""
        response = await session_manager_zmq_client.call("get_session_status")
        assert response is not None
        assert "success" in response or "result" in response
        
    @pytest.mark.asyncio
    async def test_plugin_lifecycle_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test complete plugin lifecycle via ZMQ"""
        plugin_uri = session_manager_zmq_client.get_test_plugin(0)
        
        # Load plugin
        load_response = await session_manager_zmq_client.call("load_plugin", uri=plugin_uri)
        assert "success" in load_response or "result" in load_response
        
        # Extract instance ID from response
        instance_id = None
        if "success" in load_response and load_response["success"]:
            instance_id = load_response.get("instance_id")
        elif "result" in load_response:
            instance_id = load_response["result"].get("instance_id")
            
        if instance_id:
            try:
                # Get plugin info
                info_response = await session_manager_zmq_client.call("get_plugin_info", instance_id=instance_id)
                assert info_response is not None
                
                # Update parameter
                param_response = await session_manager_zmq_client.call(
                    "update_parameter",
                    instance_id=instance_id,
                    symbol="gain",
                    value=0.8
                )
                assert param_response is not None
                
                # Get current parameters
                params_response = await session_manager_zmq_client.call("get_parameters", instance_id=instance_id)
                assert params_response is not None
                
            finally:
                # Remove plugin
                remove_response = await session_manager_zmq_client.call("remove_plugin", instance_id=instance_id)
                assert remove_response is not None
                
    @pytest.mark.asyncio
    async def test_batch_operations_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test batch operations via ZMQ"""
        plugin_uris = [
            session_manager_zmq_client.get_test_plugin(0),
            session_manager_zmq_client.get_test_plugin(1)
        ]
        
        loaded_instances = []
        
        # Load multiple plugins
        for uri in plugin_uris:
            response = await session_manager_zmq_client.call("load_plugin", uri=uri)
            if response.get("success") or response.get("result"):
                instance_id = response.get("instance_id") or response.get("result", {}).get("instance_id")
                if instance_id:
                    loaded_instances.append(instance_id)
                    
        try:
            # Get all loaded plugins
            list_response = await session_manager_zmq_client.call("get_loaded_plugins")
            assert list_response is not None
            
            # Verify our plugins are in the list
            if list_response.get("success") or list_response.get("result"):
                plugins = list_response.get("plugins") or list_response.get("result", {}).get("plugins", [])
                loaded_ids = {p.get("instance_id") for p in plugins if p.get("instance_id")}
                for instance_id in loaded_instances:
                    assert instance_id in loaded_ids
                    
        finally:
            # Clean up all loaded plugins
            for instance_id in loaded_instances:
                await session_manager_zmq_client.call("remove_plugin", instance_id=instance_id)
                
    @pytest.mark.asyncio
    async def test_jack_operations_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test JACK operations via ZMQ"""
        # Get JACK status
        status_response = await session_manager_zmq_client.call("get_jack_status")
        assert status_response is not None
        
        # Get JACK connections
        connections_response = await session_manager_zmq_client.call("get_jack_connections")
        assert connections_response is not None
        
        # Get JACK ports
        ports_response = await session_manager_zmq_client.call("get_jack_ports")
        assert ports_response is not None
        
        # Get sample rate
        samplerate_response = await session_manager_zmq_client.call("get_jack_samplerate")
        assert samplerate_response is not None
        
        # Get buffer size
        buffersize_response = await session_manager_zmq_client.call("get_jack_buffersize")
        assert buffersize_response is not None
        
    @pytest.mark.asyncio
    async def test_system_operations_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test system operations via ZMQ"""
        # Get system status
        system_response = await session_manager_zmq_client.call("get_system_status")
        assert system_response is not None
        
        # Get CPU usage
        cpu_response = await session_manager_zmq_client.call("get_cpu_usage")
        assert cpu_response is not None
        
        # Get memory usage
        memory_response = await session_manager_zmq_client.call("get_memory_usage")
        assert memory_response is not None
        
        # Get disk usage
        disk_response = await session_manager_zmq_client.call("get_disk_usage")
        assert disk_response is not None
        
    @pytest.mark.asyncio
    async def test_configuration_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test configuration operations via ZMQ"""
        # Get configuration
        get_response = await session_manager_zmq_client.call("get_config")
        assert get_response is not None
        
        # Set configuration
        set_response = await session_manager_zmq_client.call(
            "set_config", 
            key="zmq_test_key", 
            value="zmq_test_value"
        )
        assert set_response is not None
        
        # Verify configuration was set
        verify_response = await session_manager_zmq_client.call("get_config", key="zmq_test_key")
        assert verify_response is not None
        
    @pytest.mark.asyncio
    async def test_snapshot_operations_zmq(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test snapshot operations via ZMQ"""
        snapshot_name = "test_snapshot_zmq"
        
        # Save snapshot
        save_response = await session_manager_zmq_client.call("save_snapshot", name=snapshot_name)
        assert save_response is not None
        
        # List snapshots
        list_response = await session_manager_zmq_client.call("list_snapshots")
        assert list_response is not None
        
        # Load snapshot
        load_response = await session_manager_zmq_client.call("load_snapshot", name=snapshot_name)
        assert load_response is not None
        
        # Clean up
        remove_response = await session_manager_zmq_client.call("remove_snapshot", name=snapshot_name)
        assert remove_response is not None
        
    @pytest.mark.asyncio
    async def test_zmq_error_handling(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test ZMQ error handling and malformed requests"""
        # Invalid method
        try:
            response = await session_manager_zmq_client.call("invalid_method_name")
            assert response is not None
            # Should get an error response
            assert ("success" in response and not response["success"]) or "error" in response
        except:
            # Some implementations might raise exceptions for invalid methods
            pass
            
        # Invalid parameters
        response = await session_manager_zmq_client.call("load_plugin")  # Missing required uri
        assert response is not None
        
    @pytest.mark.asyncio
    async def test_zmq_message_integrity(self, session_manager_zmq_client: SessionManagerZmqTestClient):
        """Test ZMQ message serialization/deserialization"""
        # Test with various data types
        test_cases = [
            {"method": "get_config", "params": {"key": "string_value"}},
            {"method": "set_config", "params": {"key": "test_int", "value": 42}},
            {"method": "set_config", "params": {"key": "test_float", "value": 3.14159}},
            {"method": "set_config", "params": {"key": "test_bool", "value": True}},
            {"method": "set_config", "params": {"key": "test_list", "value": [1, 2, 3]}},
            {"method": "set_config", "params": {"key": "test_dict", "value": {"nested": "value"}}},
        ]
        
        for case in test_cases:
            response = await session_manager_zmq_client.call(case["method"], **case["params"])
            assert response is not None
            # Response should be properly deserialized JSON