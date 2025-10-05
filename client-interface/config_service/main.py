from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Marlise Config Service")

# Simple in-memory store for config values (for development only)
_store: Dict[str, Any] = {
    "system.version": "0.0.0",
    "system.build_date": "2025-10-05",
    "system.cloud_url": "",
    "system.pedalboards_url": "",
}


class BatchRequest(BaseModel):
    queries: Dict[str, Any]


@app.post("/api/config/settings/batch")
async def batch_settings(req: BatchRequest):
    results = {}
    for k in req.queries.keys():
        results[k] = _store.get(k)
    return {"results": results}


@app.post("/config/set")
async def config_set(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())

    # Expecting {key: value} or {"key": "k", "value": "v"}
    if "key" in data and "value" in data:
        _store[data["key"]] = data["value"]
        return {"status": "ok"}

    for k, v in data.items():
        _store[k] = v
    return {"status": "ok"}
