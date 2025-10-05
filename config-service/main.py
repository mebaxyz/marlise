"""
Config service (ZMQ-only) - robust atomic write for settings persistence.

This is a copy of the running service but with a safer _atomic_write:
- ensures the target directory exists
- logs directory state before mkstemp
- if mkstemp into the target dir fails, falls back to creating the temp
  file in the system temp dir and then moves it into place (best-effort).
"""
import asyncio
import json
import logging
import zlib
import uuid
import os
import tempfile
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
    """Write JSON data atomically to path with fallbacks.

    Strategy:
    1. Ensure parent directory exists (os.makedirs(..., exist_ok=True)).
    2. Try tempfile.mkstemp(prefix, dir=parent).
    3. If that fails (FileNotFoundError or OSError), try mkstemp() in system temp
       directory and then os.replace into the final path.
    4. Always fsync before replace and clean up temp files on error.
    """
    dirn = os.path.dirname(path) or "."

    # Make sure the directory exists and is writable if possible
    try:
        os.makedirs(dirn, exist_ok=True)
    except Exception:
        # If we can't create it, we'll still try mkstemp and surface the error
        logger.exception("Could not ensure settings directory exists: %s", dirn)

    # Log directory listing to help debugging problems with bind-mounts
    try:
        listing = os.listdir(dirn)
    except Exception as e:
        listing = f"<unable to list: {e}>"
    logger.debug("_atomic_write: dir=%s listing=%s", dirn, listing)

    tmp_path = None
    fd = None
    # First attempt: create temp file next to final file (preferred)
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp.settings.", dir=dirn)
    except Exception as e:
        logger.warning("mkstemp in target dir failed (%s). Falling back to system tempdir", e)

    # Fallback: create temp file in system tempdir
    if fd is None:
        try:
            fd, tmp_path = tempfile.mkstemp(prefix=".tmp.settings.")
        except Exception:
            # Give up with the original error
            logger.exception("Failed to create temporary file for atomic write")
            raise

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Ensure destination directory still exists before replace
        parent = os.path.dirname(path) or "."
        if not os.path.exists(parent):
            logger.warning("Parent directory disappeared before replace: %s", parent)
        os.replace(tmp_path, path)
        try:
            # Make the settings file world-readable so host user can inspect it when container
            # runs as root during development. This is a best-effort convenience step.
            os.chmod(path, 0o644)
        except Exception:
            logger.exception("Failed to chmod settings file: %s", path)
    except Exception:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            logger.exception("Failed to remove temporary file: %s", tmp_path)
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
                if method in ("get_settings", "batch_settings"):
                    queries = params.get("queries") if isinstance(params, dict) else None
                    if not isinstance(queries, dict):
                        raise ValueError("missing queries object")

                    results: Dict[str, Any] = {}
                    for key in queries.keys():
                        val = _get_by_dotted(_store, key) if isinstance(key, str) else None
                        results[key] = val

                    response = {"request_id": request_id, "result": {"results": results}, "timestamp": datetime.now().isoformat()}
                    await rpc_socket.send_json(response)

                elif method in ("set_settings", "config_set"):
                    if "key" in params and "value" in params and isinstance(params["key"], str):
                        _set_by_dotted(_store, params["key"], params["value"])
                    else:
                        if not isinstance(params, dict):
                            raise ValueError("invalid params for config_set")
                        for k, v in params.items():
                            if isinstance(k, str):
                                _set_by_dotted(_store, k, v)

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
