Config Service (ZeroMQ)

This small development service provides an in-memory configuration store accessible via ZeroMQ RPC.

Protocol
- RPC over ZeroMQ REQ/REP
- Deterministic RPC port: 5555 + (crc32(service_name) % 1000)
- Service name: "config_service"

Implemented RPC methods
- get_settings (canonical) — alias: batch_settings
  - Signature: get_settings(params={"queries": {"key": null, ...}})
  - Returns: {"results": {"key": value, ...}}
  - Behavior: For each key in the provided `queries` map the service returns the value found in the loaded settings. Keys support dotted paths for nested values (for example, "system.version" or "paths.data_dir"). If a key is not present the returned value will be null.

- set_settings (canonical) — alias: config_set
  - Signature: set_settings(params={"key": "dotted.path", "value": ...}) OR set_settings(params={"k1": v1, "k2": v2, ...})
  - Returns: {"status": "ok"} on success
  - Behavior: Sets a configuration value. Keys may be dotted paths to set nested values. When the operation succeeds the settings file (`data/settings.json`) is written atomically with the updated values.

- get_setting (single-key helper)
  - Signature: get_setting(params={"key":"dotted.path"}) OR get_setting(params="dotted.path")
  - Returns: {"value": <the value>}
  - Behavior: Convenience method to fetch a single dotted-path value.

- set_setting (single-key helper)
  - Signature: set_setting(params={"key":"dotted.path","value": ...}) OR set_setting(params=["dotted.path", value])
  - Returns: {"status": "ok"}
  - Behavior: Convenience method to set a single dotted-path value and persist the settings file.

Usage
- The client-side `ZMQClient` used in the project (e.g. client interface) can call these methods using its `call(service_name, method, ...)` API. Example: `zmq_client.call("config_service", "get_settings", queries={"system.version": None})`.

Persistence & Notes
- The service loads `data/settings.json` at startup. If the file is missing the service starts with an empty settings object.
- `set_setting` and `set_settings` persist changes atomically to `data/settings.json`.
- This service is intended for development; consider hardening, validation and access control before using it in production.
