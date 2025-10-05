"""Tests for SessionControlService."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.session_control_service import SessionControlService


@pytest.fixture
def mock_bridge_client():
    """Mock bridge client for testing."""
    mock = AsyncMock()
    mock.call.return_value = {"success": True}
    return mock


@pytest.fixture
def mock_plugin_manager():
    """Mock plugin manager for testing."""
    return AsyncMock()


@pytest.fixture
def mock_connection_service():
    """Mock connection service for testing."""
    service = MagicMock()
    service.connections = MagicMock()
    service.connections.__len__ = MagicMock(return_value=5)
    service.clear_connections = MagicMock()
    return service


@pytest.fixture
def mock_service_bus():
    """Mock service bus for testing."""
    return AsyncMock()


@pytest.fixture
def session_control_service(mock_bridge_client, mock_plugin_manager, mock_connection_service, mock_service_bus):
    """Create SessionControlService instance for testing."""
    return SessionControlService(mock_bridge_client, mock_plugin_manager, mock_connection_service, mock_service_bus)


@pytest.mark.asyncio
async def test_reset_session_success(session_control_service, mock_bridge_client, mock_plugin_manager, mock_connection_service, mock_service_bus):
    """Test successful session reset."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await session_control_service.reset_session("bank1")

    # Verify
    assert result["status"] == "ok"
    assert "Session reset successfully" in result["message"]

    mock_connection_service.clear_connections.assert_called_once()
    mock_plugin_manager.clear_all.assert_called_once()
    mock_bridge_client.call.assert_called_with("modhost_bridge", "reset_session")
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_reset_session_failure(session_control_service, mock_bridge_client, mock_plugin_manager, mock_connection_service):
    """Test session reset failure."""
    # Setup
    mock_bridge_client.call.return_value = {"success": False, "error": "Reset failed"}

    # Execute
    result = await session_control_service.reset_session()

    # Verify
    assert result["status"] == "error"
    assert "Failed to reset mod-host state" in result["message"]


@pytest.mark.asyncio
async def test_mute_session_success(session_control_service, mock_bridge_client, mock_service_bus):
    """Test successful session mute."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await session_control_service.mute_session()

    # Verify
    assert result["status"] == "ok"
    assert result["muted"] is True

    mock_bridge_client.call.assert_called_with("modhost_bridge", "mute_session")
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_unmute_session_success(session_control_service, mock_bridge_client, mock_service_bus):
    """Test successful session unmute."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await session_control_service.unmute_session()

    # Verify
    assert result["status"] == "ok"
    assert result["muted"] is False

    mock_bridge_client.call.assert_called_with("modhost_bridge", "unmute_session")
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_state(session_control_service, mock_bridge_client, mock_plugin_manager, mock_connection_service):
    """Test getting session state."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True, "data": "system_data"}
    mock_plugin_manager.instances = {"inst1": "plugin1", "inst2": "plugin2"}

    # Execute
    result = await session_control_service.get_session_state()

    # Verify
    assert "session" in result
    assert "system" in result
    assert "timestamp" in result
    assert result["session"]["active_connections"] == 5
    assert result["session"]["loaded_plugins"] == 2
    assert result["system"] == {"success": True, "data": "system_data"}


@pytest.mark.asyncio
async def test_initialize_session_success(session_control_service, mock_bridge_client, mock_plugin_manager, mock_connection_service, mock_service_bus):
    """Test successful session initialization."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await session_control_service.initialize_session()

    # Verify
    assert result["status"] == "ok"
    assert "Session initialized" in result["message"]

    mock_connection_service.clear_connections.assert_called_once()
    mock_plugin_manager.clear_all.assert_called_once()
    mock_bridge_client.call.assert_called_with("modhost_bridge", "initialize_session")
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_session_failure(session_control_service, mock_bridge_client, mock_plugin_manager, mock_connection_service):
    """Test session initialization failure."""
    # Setup
    mock_bridge_client.call.return_value = {"success": False, "error": "Init failed"}

    # Execute
    result = await session_control_service.initialize_session()

    # Verify
    assert result["status"] == "error"
    assert "Failed to initialize session" in result["message"]