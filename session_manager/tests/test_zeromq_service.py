import asyncio

import pytest
from servicebus import Service

# Import the session_manager module so tests can start the service in-process
from ..main import SessionManagerService


@pytest.mark.asyncio
async def test_health():
    # Start the session_manager service in-process
    service = SessionManagerService()
    await service.startup()
    # Give ZeroMQ sockets a moment to bind
    await asyncio.sleep(0.1)

    client = Service("test_client")
    await client.start()
    try:
        result = await asyncio.wait_for(
            client.call("session_manager", "health"), timeout=5.0
        )
        assert result["service"] == "session_manager"
        assert result["status"] == "healthy"
        assert result["details"]["service_bus_connected"] is True
    finally:
        await client.stop()
        # Shutdown the in-process service
        await service.shutdown()


@pytest.mark.asyncio
async def test_echo():
    # Start the session_manager service in-process
    service = SessionManagerService()
    await service.startup()
    # Give ZeroMQ sockets a moment to bind
    await asyncio.sleep(0.1)

    client = Service("test_client")
    await client.start()
    try:
        result = await asyncio.wait_for(
            client.call("session_manager", "echo", message="Hello MOD UI!"),
            timeout=5.0
        )
        assert result["echo"] == "Hello MOD UI!"
    finally:
        await client.stop()
        # Shutdown the in-process service
        await service.shutdown()
