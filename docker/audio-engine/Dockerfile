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
    cppzmq-dev \
    libjsoncpp-dev \
    libspdlog-dev \
    libfmt-dev \
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
COPY audio-engine/utils /src/utils

# Build mod-host (classic make-based host)
WORKDIR /src/mod-host
RUN if [ -f Makefile ]; then \
      make -j$(nproc); \
    else \
      echo "No Makefile found in mod-host; skipping mod-host build"; \
    fi

# Build utils library required by modhost-bridge
WORKDIR /src/utils
RUN if [ -f CMakeLists.txt ]; then \
            mkdir -p build && cd build && cmake .. && make -j$(nproc) && cp libmod_utils.* .. || true; \
        else \
            echo "No CMakeLists.txt found in utils; skipping utils build"; \
        fi

# Build modhost-bridge (cmake)
WORKDIR /src/modhost-bridge
RUN mkdir -p build && cd build && cmake .. && make -j$(nproc)

# Install stage: copy built binaries into a single prefix
RUN mkdir -p /opt/marlise/bin
RUN if [ -f /src/mod-host/mod-host ]; then cp /src/mod-host/mod-host /opt/marlise/bin/ || true; fi
RUN if [ -f /src/modhost-bridge/build/modhost-bridge ]; then cp /src/modhost-bridge/build/modhost-bridge /opt/marlise/bin/ || true; fi
RUN mkdir -p /opt/marlise/lib
RUN cp /src/utils/libmod_utils.* /opt/marlise/lib/ || true


FROM debian:trixie-slim AS runtime
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    jackd2 \
    libjack-jackd2-0 \
    libzmq5 \
    libjsoncpp26 \
    liblilv-0-0 \
    libfmt10 \
    libfftw3-double3 \
    alsa-utils \
    socat \
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
# Use the repository's start-service.sh which has the known working startup sequence
COPY scripts/start-service.sh /opt/marlise/start.sh
RUN chmod +x /opt/marlise/start.sh

# Ensure the start script uses the binaries we installed into /opt/marlise/bin
ENV MOD_HOST_BIN=/opt/marlise/bin/mod-host
ENV MODHOST_BRIDGE_BIN=/opt/marlise/bin/modhost-bridge

WORKDIR /opt/marlise

EXPOSE 5555 5556 6000

# Copy entrypoint that can start jackd if requested then exec start-service.sh
COPY docker/audio-engine/entrypoint.sh /opt/marlise/entrypoint.sh
RUN chmod +x /opt/marlise/entrypoint.sh

# Copy supervisord config
RUN mkdir -p /opt/logs || true

# Default entrypoint uses tini and our entrypoint wrapper to start jackd, bridge, and exec mod-host
ENTRYPOINT ["/bin/bash", "/opt/marlise/entrypoint.sh"]
CMD []
