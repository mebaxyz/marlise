This folder contains the Client Interface web API (FastAPI) moved from the legacy location under `web_client`.

During development the Docker build context points at `client-interface/web_api/api` and the container mounts `/app` to the web_api directory for live edits.
