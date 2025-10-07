#!/usr/bin/env python3
"""
Integration test for audio system management handlers in session manager.
Tests the audio system commands that communicate with modhost-bridge service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from session_manager.zmq_handlers import ZMQHandlers


class TestAudioSystemHandlers:
    """Test audio system management handlers"""

    @pytest.fixture
    def mock_bridge_client(self):
        """Mock bridge client for testing"""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_plugin_manager(self):
        """Mock plugin manager for testing"""
        manager = AsyncMock()
        return manager

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager for testing"""
        manager = AsyncMock()
        return manager

    @pytest.fixture
    def mock_service_bus(self):
        """Mock service bus for testing"""
        bus = MagicMock()
        bus.register_handler = MagicMock()
        return bus

    @pytest.fixture
    def handlers(self, mock_bridge_client, mock_plugin_manager, mock_session_manager, mock_service_bus):
        """Create handlers instance with mocked dependencies.

        We pass the `mock_service_bus` as the `zmq_service` argument so the
        handler registration uses the same `register_handler` API for tests.
        """
        return ZMQHandlers(
            mock_bridge_client,
            mock_plugin_manager,
            mock_session_manager,
            mock_service_bus,
        )

    @pytest.mark.asyncio
    async def test_init_jack_success(self, handlers, mock_bridge_client):
        """Test successful JACK initialization"""
        # Setup mock response
        mock_bridge_client.call.return_value = {"success": True}

        # Call handler
        result = await handlers.handle_init_jack()

        # Verify
        assert result == {"success": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "init_jack")

    @pytest.mark.asyncio
    async def test_init_jack_failure(self, handlers, mock_bridge_client):
        """Test JACK initialization failure"""
        # Setup mock to raise exception
        mock_bridge_client.call.side_effect = Exception("JACK init failed")

        # Call handler
        result = await handlers.handle_init_jack()

        # Verify
        assert result == {"success": False, "error": "JACK init failed"}

    @pytest.mark.asyncio
    async def test_get_jack_data_success(self, handlers, mock_bridge_client):
        """Test successful JACK data retrieval"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "cpu_load": 15.5,
            "xruns": 2,
            "rolling": True,
            "bpb": 4,
            "bpm": 120.0
        }

        # Call handler
        result = await handlers.handle_get_jack_data(with_transport=True)

        # Verify
        expected = {
            "success": True,
            "cpu_load": 15.5,
            "xruns": 2,
            "rolling": True,
            "bpb": 4,
            "bpm": 120.0
        }
        assert result == expected
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "get_jack_data", with_transport=True)

    @pytest.mark.asyncio
    async def test_get_jack_buffer_size_success(self, handlers, mock_bridge_client):
        """Test successful buffer size retrieval"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "buffer_size": 1024
        }

        # Call handler
        result = await handlers.handle_get_jack_buffer_size()

        # Verify
        assert result == {"success": True, "buffer_size": 1024}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "get_jack_buffer_size")

    @pytest.mark.asyncio
    async def test_set_jack_buffer_size_success(self, handlers, mock_bridge_client):
        """Test successful buffer size setting"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "buffer_size": 512
        }

        # Call handler
        result = await handlers.handle_set_jack_buffer_size(size=512)

        # Verify
        assert result == {"success": True, "buffer_size": 512}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "set_jack_buffer_size", size=512)

    @pytest.mark.asyncio
    async def test_set_jack_buffer_size_missing_param(self, handlers, mock_bridge_client):
        """Test buffer size setting with missing parameter"""
        # Call handler without size parameter
        result = await handlers.handle_set_jack_buffer_size()

        # Verify
        assert result == {"success": False, "error": "Missing 'size' parameter"}
        mock_bridge_client.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_jack_port_alias_success(self, handlers, mock_bridge_client):
        """Test successful port alias retrieval"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "alias": "system:capture_1"
        }

        # Call handler
        result = await handlers.handle_get_jack_port_alias(port_name="system:capture_1")

        # Verify
        assert result == {"success": True, "alias": "system:capture_1"}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "get_jack_port_alias", port_name="system:capture_1")

    @pytest.mark.asyncio
    async def test_get_jack_port_alias_missing_param(self, handlers, mock_bridge_client):
        """Test port alias retrieval with missing parameter"""
        # Call handler without port_name parameter
        result = await handlers.handle_get_jack_port_alias()

        # Verify
        assert result == {"success": False, "error": "Missing 'port_name' parameter"}
        mock_bridge_client.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_jack_hardware_ports_success(self, handlers, mock_bridge_client):
        """Test successful hardware ports retrieval"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "ports": ["system:capture_1", "system:capture_2"]
        }

        # Call handler
        result = await handlers.handle_get_jack_hardware_ports(is_audio=True, is_output=False)

        # Verify
        assert result == {"success": True, "ports": ["system:capture_1", "system:capture_2"]}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "get_jack_hardware_ports", is_audio=True, is_output=False)

    @pytest.mark.asyncio
    async def test_has_midi_beat_clock_sender_port_success(self, handlers, mock_bridge_client):
        """Test successful MIDI beat clock sender port check"""
        # Setup mock response
        mock_bridge_client.call.return_value = {
            "success": True,
            "has_port": True
        }

        # Call handler
        result = await handlers.handle_has_midi_beat_clock_sender_port()

        # Verify
        assert result == {"success": True, "has_port": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "has_midi_beat_clock_sender_port")

    @pytest.mark.asyncio
    async def test_connect_jack_ports_success(self, handlers, mock_bridge_client):
        """Test successful JACK port connection"""
        # Setup mock response
        mock_bridge_client.call.return_value = {"success": True}

        # Call handler
        result = await handlers.handle_connect_jack_ports(port1="system:capture_1", port2="effect:input")

        # Verify
        assert result == {"success": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "connect_jack_ports",
                                                       port1="system:capture_1", port2="effect:input")

    @pytest.mark.asyncio
    async def test_connect_jack_ports_missing_params(self, handlers, mock_bridge_client):
        """Test JACK port connection with missing parameters"""
        # Call handler with missing parameters
        result = await handlers.handle_connect_jack_ports(port1="system:capture_1")

        # Verify
        assert result == {"success": False, "error": "Missing 'port1' or 'port2' parameter"}
        mock_bridge_client.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnect_jack_ports_success(self, handlers, mock_bridge_client):
        """Test successful JACK port disconnection"""
        # Setup mock response
        mock_bridge_client.call.return_value = {"success": True}

        # Call handler
        result = await handlers.handle_disconnect_jack_ports(port1="system:capture_1", port2="effect:input")

        # Verify
        assert result == {"success": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "disconnect_jack_ports",
                                                       port1="system:capture_1", port2="effect:input")

    @pytest.mark.asyncio
    async def test_disconnect_all_jack_ports_success(self, handlers, mock_bridge_client):
        """Test successful disconnect all ports"""
        # Setup mock response
        mock_bridge_client.call.return_value = {"success": True}

        # Call handler
        result = await handlers.handle_disconnect_all_jack_ports(port="system:capture_1")

        # Verify
        assert result == {"success": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "disconnect_all_jack_ports", port="system:capture_1")

    @pytest.mark.asyncio
    async def test_disconnect_all_jack_ports_missing_param(self, handlers, mock_bridge_client):
        """Test disconnect all ports with missing parameter"""
        # Call handler without port parameter
        result = await handlers.handle_disconnect_all_jack_ports()

        # Verify
        assert result == {"success": False, "error": "Missing 'port' parameter"}
        mock_bridge_client.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_xruns_success(self, handlers, mock_bridge_client):
        """Test successful xruns reset"""
        # Setup mock response
        mock_bridge_client.call.return_value = {"success": True}

        # Call handler
        result = await handlers.handle_reset_xruns()

        # Verify
        assert result == {"success": True}
        mock_bridge_client.call.assert_called_once_with("modhost_bridge", "reset_xruns")

    @pytest.mark.asyncio
    async def test_service_bus_method_registration(self, handlers, mock_service_bus):
        """Test that all audio system methods are registered with ServiceBus"""
        # Call register method
        handlers.register_service_methods()

        # Verify all audio system methods were registered
        expected_registrations = [
            "init_jack",
            "close_jack",
            "get_jack_data",
            "get_jack_buffer_size",
            "set_jack_buffer_size",
            "get_jack_sample_rate",
            "get_jack_port_alias",
            "get_jack_hardware_ports",
            "has_midi_beat_clock_sender_port",
            "has_serial_midi_input_port",
            "has_serial_midi_output_port",
            "has_midi_merger_output_port",
            "has_midi_broadcaster_input_port",
            "has_duox_split_spdif",
            "connect_jack_ports",
            "connect_jack_midi_output_ports",
            "disconnect_jack_ports",
            "disconnect_all_jack_ports",
            "reset_xruns"
        ]

        # Check that register_handler was called for each method
        calls = mock_service_bus.register_handler.call_args_list
        registered_methods = [call[0][0] for call in calls]

        for method in expected_registrations:
            assert method in registered_methods, f"Method {method} not registered with ServiceBus"