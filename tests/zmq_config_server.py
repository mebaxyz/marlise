import json
import os
import signal
import tempfile
from pathlib import Path
import zmq
import zmq.asyncio
import asyncio

class ZMQConfigServer:
    def __init__(self, settings_path: Path, port: int):
        self.settings_path = settings_path
        self.port = port
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.REP)
        self._task = None

    def _load(self):
        if self.settings_path.exists():
            return json.loads(self.settings_path.read_text())
        return {}

    def _save(self, data):
        self.settings_path.write_text(json.dumps(data, indent=2))

    async def _handle(self):
        self.socket.bind(f"tcp://127.0.0.1:{self.port}")
        while True:
            msg = await self.socket.recv_json()
            method = msg.get("method")
            params = msg.get("params", {})
            data = self._load()

            if method == "get_setting":
                key = params.get("key")
                # dotted path
                parts = key.split(".") if key else []
                cur = data
                for p in parts:
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        cur = None
                        break
                await self.socket.send_json({"result": {"value": cur}})
                continue

            if method == "set_setting":
                key = params.get("key")
                value = params.get("value")
                parts = key.split(".")
                cur = data
                for p in parts[:-1]:
                    if p not in cur or not isinstance(cur[p], dict):
                        cur[p] = {}
                    cur = cur[p]
                cur[parts[-1]] = value
                self._save(data)
                await self.socket.send_json({"result": {"status": "ok"}})
                continue

            if method == "get_settings":
                queries = params.get("queries", {})
                results = {}
                for k, v in queries.items():
                    parts = v.split(".")
                    cur = data
                    for p in parts:
                        if isinstance(cur, dict) and p in cur:
                            cur = cur[p]
                        else:
                            cur = None
                            break
                    results[k] = cur
                await self.socket.send_json({"result": {"results": results}})
                continue

            if method == "set_settings":
                settings = params.get("settings", {})
                for k, v in settings.items():
                    parts = k.split(".")
                    cur = data
                    for p in parts[:-1]:
                        if p not in cur or not isinstance(cur[p], dict):
                            cur[p] = {}
                        cur = cur[p]
                    cur[parts[-1]] = v
                self._save(data)
                await self.socket.send_json({"result": {"status": "ok"}})
                continue

            await self.socket.send_json({"error": "unknown method"})

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._task = loop.create_task(self._handle())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

    def stop(self):
        try:
            self.socket.close()
            self.ctx.term()
        except Exception:
            pass
