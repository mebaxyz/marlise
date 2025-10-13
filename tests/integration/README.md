# Integration tests

This folder contains the integration test harness and helpers for the `mod-host` runtime.

Fixtures
- `modhost_image_tag` (session): builds the Docker image for the chosen stage and yields `(tag, stage)`. Use `MODHOST_TEST_STAGE` env var to pick `runtime` (default) or `builder`.
- `modhost_container` (session): starts a single detached runtime container with `JACK_DUMMY=1`, discovers the randomly published host ports for container ports `5555` (command) and `5556` (feedback), waits for mod-host readiness, and yields `(container_id, host_port, host_port_fb)`. The container is removed at session teardown.

Helpers
- `docker_helpers.py` exposes:
  - `start_runtime_container(tag)` → (container_id, host_port, host_port_fb)
  - `stop_container(container_id)`
  - `run_container_with_modhost(tag, stage)` → runs `/opt/marlise/bin/mod-host -V` inside the image and returns a CompletedProcess

Environment variables
- `MODHOST_TEST_STAGE`: `runtime` (default) or `builder` — controls which Docker image stage `modhost_image_tag` builds.
- `MODHOST_TEST_TAG`: Override the Docker image tag used for tests (default `marlise-audio:local`).

Running tests locally

Activate the test virtualenv (if used) and run pytest. Example:

```bash
. .venv-integration/bin/activate
pytest tests/integration -q
```

Quick tips for running audio-engine integration tests
----------------------------------------------------
- Use host networking for the container during local integration tests to
  avoid network namespace mismatches (recommended):

  MODHOST_TEST_USE_HOST_NETWORK=1 pytest tests/integration/...

- If you already have a `modhost-bridge` running on the host (for local
  debugging), prevent the container from starting its own bridge to avoid
  port conflicts by setting:

  SKIP_BRIDGE_IN_CONTAINER=1

  The container entrypoint will skip starting the in-container bridge when
  this variable is set. This is useful for manual debugging or when a
  separate bridge process is preferred.

Notes
- The session fixture `modhost_container` speeds up the suite by starting a single container for the entire pytest session. Tests requiring a fresh container should request their own container helper instead of the session fixture.
