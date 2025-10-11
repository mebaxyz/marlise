"""
Test configuration and fixtures for audio processing service tests.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from ..managers.plugin_manager import PluginManager
from ..managers.session_manager import SessionManager

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_servicebus():
    """Mock servicebus for testing."""
    mock = Mock()
    mock.publish_event = AsyncMock()
    mock.call = AsyncMock()
    return mock


@pytest.fixture
def mock_bridge_client():
    """Mock bridge client for testing."""
    mock = Mock()
    mock.call = AsyncMock()

    # Counter for instance IDs
    instance_counter = [0]

    # Configure default response for different bridge methods
    def mock_call(service, method, **kwargs):
        if service == "modhost_bridge":
            if method == "get_available_plugins":
                return {
                    "success": True,
                    "plugins": {
                        "http://guitarix.sourceforge.net/plugins/gx_distortion": {
                            "name": "GX Distortion",
                            "brand": "Guitarix",
                            "version": "1.0",
                            "category": "Distortion",
                            "ports": {
                                "input": {"type": "audio", "direction": "input"},
                                "output": {"type": "audio", "direction": "output"},
                                "drive": {
                                    "type": "control",
                                    "min": 0.0,
                                    "max": 1.0,
                                    "default": 0.5,
                                },
                            },
                        },
                        "http://guitarix.sourceforge.net/plugins/gx_reverb": {
                            "name": "GX Reverb",
                            "brand": "Guitarix",
                            "version": "1.0",
                            "category": "Reverb",
                            "ports": {
                                "input": {"type": "audio", "direction": "input"},
                                "output": {"type": "audio", "direction": "output"},
                                "roomsize": {
                                    "type": "control",
                                    "min": 0.0,
                                    "max": 1.0,
                                    "default": 0.5,
                                },
                                "wet": {"type": "control", "min": 0.0, "max": 1.0, "default": 0.3},
                            },
                        },
                    }
                }
            elif method == "load_plugin":
                instance_counter[0] += 1
                return {"success": True, "instance_id": f"test_instance_{instance_counter[0]}"}
            elif method == "get_plugin_essentials":
                return {
                    "success": True,
                    "essentials": {
                        "parameters": [
                            {
                                "symbol": "drive",
                                "name": "Drive",
                                "default": 0.5,
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "valid": True
                            }
                        ]
                    }
                }
        return {"success": True}

    mock.call.side_effect = mock_call
    return mock


@pytest_asyncio.fixture
async def plugin_manager(mock_servicebus, mock_bridge_client):
    """Create PluginManager instance for testing."""
    manager = PluginManager(mock_bridge_client, mock_servicebus)
    await manager.initialize()
    return manager


@pytest.fixture
def session_manager(mock_servicebus, plugin_manager, mock_bridge_client):
    """Create SessionManager instance for testing."""
    return SessionManager(plugin_manager, mock_bridge_client, mock_servicebus)


@pytest.fixture
def sample_plugin_info():
    """Sample plugin information for testing."""
    return {
        "uri": "http://example.com/plugins/reverb",
        "name": "Test Reverb",
        "brand": "Test Audio",
        "version": "1.0.0",
        "license": "GPL",
        "comment": "A test reverb plugin",
        "ports": {
            "audio": {
                "input": [{"index": 0, "name": "Audio In", "symbol": "in"}],
                "output": [{"index": 1, "name": "Audio Out", "symbol": "out"}],
            },
            "control": [
                {
                    "index": 2,
                    "name": "Room Size",
                    "symbol": "room_size",
                    "default": 0.5,
                    "minimum": 0.0,
                    "maximum": 1.0,
                }
            ],
        },
    }


@pytest.fixture
def sample_pedalboard():
    """Sample pedalboard data for testing."""
    return {
        "title": "Test Pedalboard",
        "width": 3840,
        "height": 2160,
        "plugins": [
            {
                "instance": 1,
                "uri": "http://example.com/plugins/reverb",
                "x": 100,
                "y": 100,
                "ports": {"room_size": 0.7},
            }
        ],
        "connections": [
            {"source": "system:capture_1", "target": "effect_1:in"},
            {"source": "effect_1:out", "target": "system:playback_1"},
        ],
    }
