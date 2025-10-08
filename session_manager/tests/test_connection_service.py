"""Tests for ConnectionService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from ..services.connection_service import ConnectionService
from ..models.connection import Connection


@pytest.fixture
def mock_bridge_client():
    """Mock bridge client for testing."""
    mock = AsyncMock()
    mock.call.return_value = {"success": True}
    return mock


@pytest.fixture
def mock_pedalboard_service():
    """Mock pedalboard service for testing."""
    service = MagicMock()
    service.current_pedalboard = None
    return service


@pytest.fixture
def mock_service_bus():
    """Mock service bus for testing."""
    return AsyncMock()


@pytest.fixture
def mock_plugin_manager():
    """Mock plugin manager for testing."""
    mock = Mock()
    mock.instances = {"plugin1": "mock_instance1", "plugin2": "mock_instance2"}
    return mock


@pytest.fixture
def connection_service(mock_bridge_client, mock_pedalboard_service, mock_plugin_manager, mock_service_bus):
    """Create ConnectionService instance for testing."""
    return ConnectionService(mock_bridge_client, mock_pedalboard_service, mock_plugin_manager, mock_service_bus)


@pytest.mark.asyncio
async def test_create_connection_success(connection_service, mock_bridge_client, mock_service_bus):
    """Test successful connection creation."""
    # Setup
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await connection_service.create_connection("plugin1", "out", "plugin2", "in")

    # Verify
    assert result["connection_id"] is not None
    assert result["connection"]["source_plugin"] == "plugin1"
    assert result["connection"]["source_port"] == "out"
    assert result["connection"]["target_plugin"] == "plugin2"
    assert result["connection"]["target_port"] == "in"

    mock_bridge_client.call.assert_called_with("modhost_bridge", "create_connection", source_plugin="plugin1", source_port="out", target_plugin="plugin2", target_port="in")
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_create_connection_failure(connection_service, mock_bridge_client):
    """Test connection creation failure."""
    # Setup
    mock_bridge_client.call.return_value = {"success": False, "error": "Bridge error"}

    # Execute & Verify
    with pytest.raises(RuntimeError, match="Bridge error"):
        await connection_service.create_connection("plugin1", "out", "plugin2", "in")


@pytest.mark.asyncio
async def test_remove_connection_success(connection_service, mock_bridge_client, mock_service_bus):
    """Test successful connection removal."""
    # Setup
    connection = Connection("plugin1", "out", "plugin2", "in")
    connection_service.connections.append(connection)
    mock_bridge_client.call.return_value = {"success": True}

    # Execute
    result = await connection_service.remove_connection(connection.connection_id)

    # Verify
    assert result["status"] == "ok"
    assert result["connection_id"] == connection.connection_id
    assert len(connection_service.connections) == 0

    mock_bridge_client.call.assert_called_with("modhost_bridge", "remove_connection", connection_id=connection.connection_id)
    mock_service_bus.publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_remove_connection_not_found(connection_service):
    """Test removing non-existent connection."""
    with pytest.raises(ValueError, match="Connection not found"):
        await connection_service.remove_connection("nonexistent")


def test_get_connections(connection_service):
    """Test getting all connections."""
    # Setup
    conn1 = Connection("p1", "out", "p2", "in")
    conn2 = Connection("p2", "out", "p3", "in")
    connection_service.connections.append(conn1)
    connection_service.connections.append(conn2)

    # Execute
    connections = connection_service.get_connections()

    # Verify
    assert len(connections) == 2
    assert connections[0] == conn1
    assert connections[1] == conn2


def test_clear_connections(connection_service):
    """Test clearing all connections."""
    # Setup
    connection_service.connections.append(Connection("p1", "out", "p2", "in"))
    connection_service.connections.append(Connection("p2", "out", "p3", "in"))

    # Execute
    connection_service.clear_connections()

    # Verify
    assert len(connection_service.connections) == 0