# Development nginx / static-site

This directory contains development Docker assets to serve the web client and proxy API/WebSocket requests to the local services.

Usage (development)

- Build and run only the static-site (nginx) service:

```bash
docker compose -f docker/docker-compose.dev.yml up --build static-site
```

- To run the full dev stack (client-api, session-manager, static-site):

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

Waiting for dependent services

The nginx image includes a small entrypoint wrapper that can wait for dependent services before starting nginx. Set the `WAIT_FOR_TARGETS` environment variable on the `static-site` service (in the compose file or at runtime) with a comma-separated list of targets to wait for. Targets can be either `host:port` for a TCP check or a full HTTP URL for an HTTP healthcheck.

Examples

- Wait for a local client API (port 8080) and session manager (5718):

```yaml
services:
  static-site:
    environment:
      - WAIT_FOR_TARGETS=127.0.0.1:8080,127.0.0.1:5718
```

- Wait for an HTTP health endpoint:

```yaml
      - WAIT_FOR_TARGETS=http://127.0.0.1:8080/health
```

Notes

- The `scripts/wait-for.sh` helper is copied into the image and used by the entrypoint wrapper. It accepts `--timeout` and `--interval` options.
- The development compose file uses bind-mounts for service sources so you can edit code locally and see changes in running containers.
This folder contains Docker artifacts to serve the project's static files using nginx.

Files added
- `Dockerfile` - production image that copies `docker/nginx.conf` and `static/` into the image.
- `nginx.conf` - default nginx configuration used in the image (can be overridden with a mount).
- `docker-compose.dev.yml` - development compose file that mounts the host `nginx.conf` and the project's `static/` directory into the container for live editing.

Usage

Prerequisites: Docker and docker-compose.

Development (mounts local files so you can edit them):

1. Ensure your static files are in `client-interface/web_client_wo_template/static` at the repository root.
2. From the `marlise/docker` directory run:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Open http://localhost:8080 to view the static site.

Production image build (bundles files into the image):

From repository root run:

```bash
docker build -f docker/Dockerfile -t marlise-static:latest .
docker run --rm -p 8080:80 marlise-static:latest
```

Notes and assumptions
- This setup assumes your static files live under the `static/` directory at the repo root. If your project uses a different path, update `docker/Dockerfile` and `docker-compose.dev.yml` accordingly.
- In development the `nginx.conf` and static files are mounted read-only into the container.
- The default nginx configuration is intentionally simple; adapt caching, TLS, headers, or root path to your needs.
