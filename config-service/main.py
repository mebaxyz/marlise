"""
Config service (top-level implementation)
"""
import asyncio
import json
import logging
import zlib
import uuid
from datetime import datetime
from typing import Any, Dict

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# In-memory store (development only)
_store: Dict[str, Any] = {}
_settings_path = "data/settings.json"


def _load_settings():
    """Load settings from JSON file into _store nested dict."""
    import os, json

    global _store
    try:
        if os.path.exists(_settings_path):
            with open(_settings_path, "r", encoding="utf-8") as f:
                _store = json.load(f)
                logger.info("Loaded settings from %s", _settings_path)
        else:
            logger.warning("Settings file %s not found, starting with empty settings", _settings_path)
            _store = {}
    except Exception as e:
        logger.exception("Failed to load settings: %s", e)
        _store = {}


def _atomic_write(path: str, data: dict):
    """Write JSON data atomically to path."""
    import json, os, tempfile, shutil

    dirn = os.path.dirname(path) or "."
    # Ensure target directory exists
    os.makedirs(dirn, exist_ok=True)

    fd = None
    tmp = None
    try:
        # Create temp file in the same directory to allow atomic replace
        fd, tmp = tempfile.mkstemp(prefix=".tmp.settings.", dir=dirn)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Try atomic replace
        try:
            os.replace(tmp, path)
            return
        except OSError as e:
            # Cross-device link or other issue; attempt safe fallback
            logger.warning("os.replace failed (%s), falling back to copy", e)
            try:
                shutil.copyfile(tmp, path)
                os.remove(tmp)
                return
            except Exception:
                # Last-resort: write directly (not atomic)
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    if tmp and os.path.exists(tmp):
                        os.remove(tmp)
                    return
                except Exception:
                    raise
    except Exception:
        # Clean up temp file on failure
        try:
            if fd:
                os.close(fd)
        except Exception:
            pass
        try:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        raise


def _get_by_dotted(store: dict, path: str):
    parts = path.split(".")
    node = store
    for p in parts:
        if isinstance(node, dict) and p in node:
            node = node[p]
        else:
            return None
    return node


def _set_by_dotted(store: dict, path: str, value):
    parts = path.split(".")
    node = store
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value


def _assign_rpc_port(service_name: str, base_port: int = 5555) -> int:
    service_hash = zlib.crc32(service_name.encode("utf-8")) % 1000
    return base_port + service_hash


async def handle_requests(service_name: str = "config_service") -> None:
    ctx = zmq.asyncio.Context()
    rpc_port = _assign_rpc_port(service_name)
    rpc_socket = ctx.socket(zmq.REP)
    bind_addr = f"tcp://127.0.0.1:{rpc_port}"
    rpc_socket.bind(bind_addr)

    logger.info("Config service '%s' listening on %s", service_name, bind_addr)

    # Load settings file at startup
    _load_settings()

    try:
        while True:
            try:
                msg = await rpc_socket.recv_json()
            except Exception as e:
                logger.exception("Failed to receive message: %s", e)
                await asyncio.sleep(0.1)
                continue

            request_id = msg.get("request_id") or str(uuid.uuid4())
            method = msg.get("method")
            params = msg.get("params") or {}

            logger.debug("Received RPC: %s params=%s", method, params)

            try:
                # Accept both the new canonical names and older aliases for compatibility
                if method in ("get_settings", "batch_settings"):
                    queries = params.get("queries") if isinstance(params, dict) else None
                    if not isinstance(queries, dict):
                        raise ValueError("missing queries object")

                    results: Dict[str, Any] = {}
                    for key in queries.keys():
                        # support dotted keys into nested settings
                        val = _get_by_dotted(_store, key) if isinstance(key, str) else None
                        results[key] = val

                    response = {"request_id": request_id, "result": {"results": results}, "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)

                elif method in ("set_settings", "config_set"):
                    # Accept either {key:..., value:...} or an arbitrary dict of key->value
                    if "key" in params and "value" in params and isinstance(params["key"], str):
                        _set_by_dotted(_store, params["key"], params["value"])
                    else:
                        # set all provided keys (top-level or dotted)
                        if not isinstance(params, dict):
                            raise ValueError("invalid params for config_set")
                        for k, v in params.items():
                            if isinstance(k, str):
                                _set_by_dotted(_store, k, v)

                    # Persist settings file
                    try:
                        _atomic_write(_settings_path, _store)
                    except Exception as e:
                        logger.exception("Failed to persist settings: %s", e)
                        response = {"request_id": request_id, "error": f"persist_error: {e}", "timestamp": datetime.now().isoformat()}
                        await rpc_socket.send_json(response)
                        continue

                    response = {"request_id": request_id, "result": {"status": "ok"}, "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)
                elif method in ("get_setting",):
                    # params may be a dict {'key': 'a.b'} or a raw string 'a.b'
                    key = None
                    if isinstance(params, str):
                        key = params
                    elif isinstance(params, dict):
                        key = params.get("key")

                    if not isinstance(key, str):
                        raise ValueError("missing key for get_setting")

                    val = _get_by_dotted(_store, key)
                    response = {"request_id": request_id, "result": {"value": val}, "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)

                elif method in ("set_setting",):
                    # Accept single-parameter forms: dict {"key":k, "value":v} or list/tuple [k,v]
                    key = None
                    value = None
                    if isinstance(params, dict) and "key" in params and "value" in params:
                        key = params.get("key")
                        value = params.get("value")
                    elif isinstance(params, (list, tuple)) and len(params) >= 2:
                        key = params[0]
                        value = params[1]

                    if not isinstance(key, str):
                        raise ValueError("missing key for set_setting")

                    _set_by_dotted(_store, key, value)
                    try:
                        _atomic_write(_settings_path, _store)
                    except Exception as e:
                        logger.exception("Failed to persist settings: %s", e)
                        response = {"request_id": request_id, "error": f"persist_error: {e}", "timestamp": datetime.now().isoformat()}
                        await rpc_socket.send_json(response)
                        continue

                    response = {"request_id": request_id, "result": {"status": "ok"}, "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)

                else:
                    response = {"request_id": request_id, "error": f"Method '{method}' not found", "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)

            except Exception as e:
                logger.exception("Handler error for %s: %s", method, e)
                response = {"request_id": request_id, "error": str(e), "timestamp": datetime.now().isoformat()}
                try:
                    await rpc_socket.send_json(response)
                except Exception:
                    # If sending fails, log and continue
                    logger.exception("Failed to send error response")

    finally:
        try:
            rpc_socket.close()
        except Exception:
            pass
        ctx.term()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(handle_requests())
    except KeyboardInterrupt:
        logger.info("Config service shutting down")


if __name__ == "__main__":
    main()
