import importlib.util
import types
import sys
from pathlib import Path
import uvicorn

def create_package_mapping(repo_root: Path):
    api_dir = repo_root / "client-interface" / "web_client" / "api"
    pkg_base = types.ModuleType("client_interface")
    pkg_base.__path__ = [str(repo_root / "client-interface")]
    pkg_web = types.ModuleType("client_interface.web_client")
    pkg_web.__path__ = [str(repo_root / "client-interface" / "web_client")]
    pkg_api = types.ModuleType("client_interface.web_client.api")
    pkg_api.__path__ = [str(api_dir)]
    sys.modules["client_interface"] = pkg_base
    sys.modules["client_interface.web_client"] = pkg_web
    sys.modules["client_interface.web_client.api"] = pkg_api
    return api_dir

def load_app_module(api_dir: Path):
    main_path = api_dir / "main.py"
    spec = importlib.util.spec_from_file_location("client_interface.web_client.api.main", str(main_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    api_dir = create_package_mapping(repo_root)
    app_mod = load_app_module(api_dir)

    # Run uvicorn programmatically on 127.0.0.1:8080
    uvicorn.run(app_mod.app, host="127.0.0.1", port=8080)
