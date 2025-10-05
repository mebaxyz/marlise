import asyncio

import pytest
from servicebus import Service

# Import the session_manager module so tests can start the service in-process
from mod_ui.services.session_manager import main as session_manager_main


@pytest.mark.asyncio
async def test_health():
    # Start the session_manager service in-process
    await session_manager_main.startup()
    # Give ZeroMQ sockets a moment to bind
    await asyncio.sleep(0.1)

    service = Service("test_client")
    await service.start()
    try:
        result = await asyncio.wait_for(
            service.call("session_manager", "health"), timeout=5.0
        )
        assert result["service"] == "session_manager"
        assert result["status"] == "healthy"
        assert result["details"]["service_bus_connected"] is True
    finally:
        await service.stop()
        # Shutdown the in-process service
        await session_manager_main.shutdown()


@pytest.mark.asyncio
async def test_echo():
    # Start the session_manager service in-process
    await session_manager_main.startup()
    # Give ZeroMQ sockets a moment to bind
    await asyncio.sleep(0.1)

    service = Service("test_client")
    await service.start()
    try:
        result = await asyncio.wait_for(
            service.call("session_manager", "echo", message="Hello MOD UI!"),
            timeout=5.0,
        )
        assert result["echo"] == "Hello MOD UI!"
    finally:
        await service.stop()
        # Shutdown the in-process service
        await session_manager_main.shutdown()
