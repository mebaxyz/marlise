import asyncio
import os

import pytest

from ..main import SessionManagerService


# This test is an integration test and requires a real modhost-bridge to be
# available. To run it, set USE_REAL_BRIDGE=1 in your environment. This avoids
# any simulation/dummy behavior and ensures we test against your real host.
if os.environ.get("USE_REAL_BRIDGE", "0") != "1":
    pytest.skip("Integration test: set USE_REAL_BRIDGE=1 to run against a real bridge", allow_module_level=True)


@pytest.mark.asyncio
async def test_auto_create_default_pedalboard():
    # Ensure the env var is present so session-manager will auto-create
    os.environ["SESSION_MANAGER_AUTO_CREATE_DEFAULT"] = "1"

    # Create and start the service (will use the real BridgeClient)
    service = SessionManagerService()
    await service.startup()

    # Give some time for the create_pedalboard task to run
    await asyncio.sleep(0.5)

    try:
        assert service.session_manager is not None
        pb = getattr(service.session_manager, "current_pedalboard", None)
        assert pb is not None, "Expected a default pedalboard to be created"
        assert getattr(pb, "name", "") == "Default"
    finally:
        # Ensure clean shutdown
        await service.shutdown()
