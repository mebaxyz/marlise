import asyncio
import os
import json

import pytest

from ..main import SessionManagerService


# Run against a real bridge only
if os.environ.get("USE_REAL_BRIDGE", "0") != "1":
    pytest.skip("Integration test: set USE_REAL_BRIDGE=1 to run against a real bridge", allow_module_level=True)


@pytest.mark.asyncio
async def test_load_minimal_pedalboard():
    os.environ["SESSION_MANAGER_AUTO_CREATE_DEFAULT"] = "0"

    # sample minimal pedalboard: no plugins to avoid external plugin dependencies
    sample_pb = {
        "id": "pb_test_1",
        "name": "Integration Test PB",
        "description": "",
        "plugins": [],
        "connections": []
    }

    service = SessionManagerService()
    await service.startup()

    # Give plugin manager a moment to populate available_plugins
    await asyncio.sleep(0.5)

    try:
        # Call load_pedalboard via session manager
        result = await service.session_manager.load_pedalboard(sample_pb)
        assert result.get("status") == "ok"
        # Check that current_pedalboard is set in memory (we avoid persisting in this test)
        assert service.session_manager.current_pedalboard is not None
        assert service.session_manager.current_pedalboard.name == "Integration Test PB"

    finally:
        await service.shutdown()
