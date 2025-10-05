Config service (ZMQ-only)
=========================

This is a small ZeroMQ-backed configuration service used by the client interface.

Rebuild and run (development):

1. Build the image:

   docker build -t marlise-config-service-dev -f config-service/Dockerfile .

2. Run the container (bind-mount host data directory so settings persist):

   docker run --name marlise-config-service-dev --rm -v "$(pwd)/data:/app/data" --network host marlise-config-service-dev

Note: In development you may prefer to run with host networking so the deterministic ZMQ port bound to 127.0.0.1 is reachable by local clients.
