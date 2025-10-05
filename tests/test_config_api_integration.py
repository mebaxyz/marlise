import json
import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
import importlib.util
import types
import sys
from pathlib import Path

# Load the FastAPI app module by file path and create a synthetic package
repo_root = Path(__file__).resolve().parents[1]
api_dir = repo_root / "client-interface" / "web_client" / "api"
zmq_path = api_dir / "zmq_client.py"
main_path = api_dir / "main.py"

# Create package modules to allow relative imports (client_interface.web_client.api)
pkg_base = types.ModuleType("client_interface")
pkg_base.__path__ = [str(repo_root / "client-interface")]
pkg_web = types.ModuleType("client_interface.web_client")
pkg_web.__path__ = [str(repo_root / "client-interface" / "web_client")]
pkg_api = types.ModuleType("client_interface.web_client.api")
pkg_api.__path__ = [str(api_dir)]

sys.modules["client_interface"] = pkg_base
sys.modules["client_interface.web_client"] = pkg_web
sys.modules["client_interface.web_client.api"] = pkg_api

# Load zmq_client as client_interface.web_client.api.zmq_client
spec = importlib.util.spec_from_file_location(
    "client_interface.web_client.api.zmq_client", str(zmq_path)
)
zmq_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zmq_mod)
sys.modules["client_interface.web_client.api.zmq_client"] = zmq_mod

# Load main as client_interface.web_client.api.main
spec = importlib.util.spec_from_file_location(
    "client_interface.web_client.api.main", str(main_path)
)
api_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_main)
sys.modules["client_interface.web_client.api.main"] = api_main


def _get_by_dotted(store: dict, path: str):
    parts = path.split(".")
    cur = store
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def _set_by_dotted(store: dict, path: str, value):
    parts = path.split(".")
    cur = store
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


class FakeZMQClient:
    def __init__(self, settings_path: Path):
        self.settings_path = settings_path

    async def start(self):
        return True

    async def stop(self):
        return True

    def is_connected(self):
        return True

    async def call(self, service_name: str, method: str, timeout: float = 5.0, **kwargs):
        # Synchronous file-based implementation for tests
        data = json.loads(self.settings_path.read_text())

        if method == "get_setting":
            key = kwargs.get("key")
            return {"value": _get_by_dotted(data, key)}

        if method == "set_setting":
            key = kwargs.get("key")
            value = kwargs.get("value")
            _set_by_dotted(data, key, value)
            # persist
            self.settings_path.write_text(json.dumps(data, indent=2))
            return {"status": "ok"}

        if method == "get_settings":
            queries = kwargs.get("queries", {})
            results = {k: _get_by_dotted(data, v) for k, v in queries.items()}
            return {"results": results}

        if method == "set_settings":
            settings = kwargs.get("settings", {})
            for k, v in settings.items():
                _set_by_dotted(data, k, v)
            self.settings_path.write_text(json.dumps(data, indent=2))
            return {"status": "ok"}

        raise RuntimeError("Unknown method")


def test_config_api_end_to_end(tmp_path):
    # Create a minimal settings.json in a temporary location for the test
    working = tmp_path / "settings.json"
    minimal = {
        "test": {"value": "initial"},
        "general": {"cloud-terms-accepted": "false"}
    }
    working.write_text(json.dumps(minimal, indent=2))

    try:

        # Install fake zmq client into the API module
        fake = FakeZMQClient(working)
        api_main.zmq_client = fake

        client = TestClient(api_main.app)

        # 1) set a single setting
        resp = client.post("/api/config/setting", json={"key": "test.integration.foo", "value": "bar"})
        assert resp.status_code == 200, resp.text
        assert working.exists()
        data = json.loads(working.read_text())
        assert data.get("test", {}).get("integration", {}).get("foo") == "bar"

        # 2) batch set multiple settings
        batch = {"settings": {"test.integration.k1": 1, "test.integration.k2": 2}}
        resp = client.post("/api/config/settings", json=batch)
        assert resp.status_code == 200, resp.text
        data = json.loads(working.read_text())
        assert data["test"]["integration"]["k1"] == 1
        assert data["test"]["integration"]["k2"] == 2

        # 3) batch get
        queries = {"queries": {"k1": "test.integration.k1", "k2": "test.integration.k2"}}
        resp = client.post("/api/config/settings/batch", json=queries)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("results", {}).get("k1") == 1
        assert body.get("results", {}).get("k2") == 2

    finally:
        # cleanup temporary working file
        try:
            working.unlink()
        except Exception:
            pass