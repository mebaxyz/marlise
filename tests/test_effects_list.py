import asyncio
from fastapi.testclient import TestClient

import api.main as main


class DummyZMQClient:
    async def call(self, service_name: str, method: str, timeout: float = 5.0, **kwargs):
        # Return a sample list of plugin descriptors
        return [
            {
                "uri": "http://example.org/plugins/plug1",
                "name": "PlugOne",
                "category": ["Modulation"],
                "version": "1.2.3",
                "microVersion": 0,
                "minorVersion": 2,
                "release": 3,
                "builder": "builder-a",
            },
            {
                "uri": "http://example.org/plugins/plug2",
                "name": "PlugTwo",
                "category": ["Delay"],
                "version": "0.1.0",
                "microVersion": 1,
                "minorVersion": 0,
                "release": 0,
                "builder": "builder-b",
            },
        ]


def test_effects_list_success():
    """Unit test for /effect/list endpoint using a mocked ZMQ client"""
    # Backup original zmq_client and replace with dummy
    orig = main.zmq_client
    main.zmq_client = DummyZMQClient()

    client = TestClient(main.app)

    try:
        resp = client.get("/effect/list")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["uri"] == "http://example.org/plugins/plug1"
        assert data[0]["name"] == "PlugOne"
        assert data[1]["category"] == ["Delay"]
    finally:
        # Restore original
        main.zmq_client = orig
