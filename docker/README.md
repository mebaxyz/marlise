This folder contains Docker artifacts to serve the project's static files using nginx.

Files added
- `Dockerfile` - production image that copies `docker/nginx.conf` and `static/` into the image.
- `nginx.conf` - default nginx configuration used in the image (can be overridden with a mount).
- `docker-compose.dev.yml` - development compose file that mounts the host `nginx.conf` and the project's `static/` directory into the container for live editing.

Usage

Prerequisites: Docker and docker-compose.

Development (mounts local files so you can edit them):

1. Ensure your static files are in `client-interface/web_client/static` at the repository root.
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
