# Stage 1: The Build and Final Image
# This is a single-stage build that includes all dependencies.
FROM debian:bookworm

# Set environment variables.
ENV REBUILD=true
ENV DEBIAN_FRONTEND=noninteractive

ARG TARGETARCH

RUN echo "Architecture is: ${TARGETARCH}" && \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        echo "Installing amd64 package"; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        echo "Installing arm64 package"; \
    else \
        echo "Unsupported architecture: ${TARGETARCH}" && exit 1; \
    fi


# Run the initial setup and install base dependencies needed for the next steps.
# Add ca-certificates to fix the certificate trust issue.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        dpkg-dev \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Now that wget is installed, we can safely use it to download and install
# the KX Studio repo.
RUN dpkg --purge kxstudio-repos-gcc5 || true && \
    wget https://launchpad.net/~kxstudio-debian/+archive/kxstudio/+files/kxstudio-repos_10.0.3_all.deb && \
    dpkg -i kxstudio-repos_10.0.3_all.deb && \
    rm kxstudio-repos_10.0.3_all.deb

# Update apt-get after adding the new repo.
RUN apt-get update

RUN dpkg --purge kxstudio-repos-gcc5 && \
    wget https://launchpad.net/~kxstudio-debian/+archive/kxstudio/+files/kxstudio-repos_10.0.3_all.deb && \
    dpkg -i kxstudio-repos_10.0.3_all.deb && \
    if [ "$TARGETARCH" = "amd64" ]; then \
        wget http://ftp.it.debian.org/debian/pool/main/l/lv2/lv2-dev_1.18.4-2_amd64.deb && \
        dpkg -i lv2-dev_1.18.4-2_amd64.deb; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        wget http://ftp.it.debian.org/debian/pool/main/l/lv2/lv2-dev_1.18.4-2_arm64.deb && \
        dpkg -i lv2-dev_1.18.4-2_arm64.deb; \
    else \
        echo "Unsupported architecture: $TARGETARCH" && exit 1; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreadline-dev \
        liblilv-dev \
        lilv-utils \
        libfftw3-dev \
        libjack-jackd2-dev \
        git \
        python3 \
        python3.11 \
        kxstudio-meta-audio-plugins \
        kxstudio-meta-audio-plugins-lv2 \
        build-essential

# Fix for Debian 12 lilv. This is architecture-independent.
RUN ln -s /usr/include/lilv-0/lilv /usr/include/lilv

# Build mod-host in this single stage.
RUN git clone https://github.com/moddevices/mod-host.git /mod/mod-host/source && \
    make -C /mod/mod-host/source

# Install gosu.
ARG GOSU_VERSION=1.12
RUN dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch" && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true

# Define build arguments for PUID and PGID.
ARG PUID=1000
ARG PGID=1000

# Create the user and group with the correct permissions.
RUN set -ex; \
    groupadd -g "$PGID" abc; \
    useradd -m -d /mod -g "$PGID" -u "$PUID" -G audio abc; \
    chown -R "$PUID":"$PGID" /mod

# This is a direct copy, since we're in a single stage.
# The binary is already in the image because we built it above.
RUN cp /mod/mod-host/source/mod-host /usr/local/bin/mod-host

# Set the entrypoint to the main executable.
ENTRYPOINT ["gosu", "abc", "mod-host"]

# Provide default arguments to the entrypoint.
CMD ["-v", "-n", "-p", "5555", "-f", "5556"]
