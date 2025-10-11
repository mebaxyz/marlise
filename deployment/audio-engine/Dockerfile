# Copied from deployment/docker/Dockerfile
FROM debian:trixie-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies (include LV2 and plugin host headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    wget \
    ca-certificates \
    libjack-jackd2-dev \
    libasound2-dev \
    libsndfile1-dev \
    libsamplerate0-dev \
    libfftw3-dev \
    libzmq3-dev \
    libjsoncpp-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libreadline-dev \
    liblilv-dev \
    lv2-dev \
    libserd-dev \
    libsord-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy only required source folders to keep context small (expects repo at build context root)
COPY audio-engine/mod-host /src/mod-host
COPY audio-engine/modhost-bridge /src/modhost-bridge

# Build mod-host (classic make-based host)
WORKDIR /src/mod-host
RUN if [ -f Makefile ]; then \
      make -j$(nproc); \
    else \
      echo "No Makefile found in mod-host; skipping mod-host build"; \
    fi

# Build modhost-bridge (cmake)
WORKDIR /src/modhost-bridge
RUN mkdir -p build && cd build && cmake .. && make -j$(nproc)

# Install stage: copy built binaries into a single prefix
RUN mkdir -p /opt/marlise/bin
RUN if [ -f /src/mod-host/mod-host ]; then cp /src/mod-host/mod-host /opt/marlise/bin/ || true; fi
RUN if [ -f /src/modhost-bridge/build/modhost-bridge ]; then cp /src/modhost-bridge/build/modhost-bridge /opt/marlise/bin/ || true; fi


FROM debian:trixie-slim AS runtime
ENV DEBIAN_FRONTEND=noninteractive

# Runtime dependencies (minimal for JACK + audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    jackd2 \
    libjack-jackd2-0 \
    alsa-utils \
    socat \
    tini \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create runtime directories and user
ENV MARLISE_USER=marlise
ENV MARLISE_UID=1000
ENV MARLISE_GID=1000
RUN groupadd -g ${MARLISE_GID} ${MARLISE_USER} || true && \
    useradd -m -u ${MARLISE_UID} -g ${MARLISE_GID} -s /bin/bash ${MARLISE_USER} || true

# Copy built artifacts from builder
COPY --from=builder /opt/marlise /opt/marlise

# Add start script (moved to audio-engine directory)
COPY deployment/audio-engine/start.sh /opt/marlise/start.sh
RUN chmod +x /opt/marlise/start.sh

WORKDIR /opt/marlise

EXPOSE 5555 5556 6000

# Default entrypoint runs the start script as non-root user (will use su-exec-like pattern)
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/marlise/start.sh"]
