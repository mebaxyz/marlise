# Start from a minimal base image that is good for containers
# Using a slim or alpine variant would be even better for size
FROM python:3.9.23-trixie

# Automatically get the target architecture from the build environment.
ARG TARGETARCH



# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive
ENV REBUILD=true

# Define default build-time arguments
ARG PUID=1000
ARG PGID=1000
# Set environment variables for runtime use
ENV PUID=${PUID}
ENV PGID=${PGID}

# --- s6-overlay Integration (multi-arch) ---
# Define the s6-overlay version.
ENV S6_VERSION="3.2.1.0"


# Dynamically download and install the correct s6-overlay tarball.
RUN case "${TARGETARCH}" in \
    "amd64") S6_ARCH="x86_64" ;; \
    "arm64") S6_ARCH="aarch64" ;; \
    "arm") S6_ARCH="armhf" ;; \
    *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac && \
    wget -O /tmp/s6-overlay.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -Jxvf /tmp/s6-overlay.tar.xz -C /



# Use bash shell
SHELL ["/bin/bash", "-c"]

# --- Dependency Installation ---
# Install base dependencies including jackd2 and gosu
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        curl \
        git \
        build-essential \
        cmake \
        python3-pip \
        jackd2 \
        libjack-jackd2-dev \
        libasound2-dev \
        liblilv-dev \
        lv2-dev \
        lilv-utils \
        libreadline-dev \
        libfftw3-dev \
        libjpeg-dev \
        zlib1g-dev \
        gosu && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

# --- Application Builds ---
# Build mod-host
RUN git clone https://github.com/mod-audio/mod-host.git /mod/mod-host/source && \
    mkdir -p /usr/include/lilv && \
    cp /usr/include/lilv-0/lilv/lilv.h /usr/include/lilv/ && \
    make -C /mod/mod-host/source && \
    make install -C /mod/mod-host/source

# Build mod-midi-merger
RUN git clone https://github.com/mod-audio/mod-midi-merger.git /mod/mod-midi-merger && \
    cd /mod/mod-midi-merger && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    cp mod-midi-merger-standalone /usr/local/bin && \
    chmod +x /usr/local/bin/mod-midi-merger-standalone

# Build mod-ui
RUN git clone https://github.com/mod-audio/mod-ui.git /mod/mod-ui

# Install Python requirements and fix tornado compatibility
RUN pip3 install -r /mod/mod-ui/requirements.txt

# Build mod-ui utils and set permissions
RUN make -C /mod/mod-ui/utils && \
    chown :audio -R /mod/mod-ui && \
    chmod -R 775 /mod/mod-ui

# Create user and group
RUN groupadd -g ${PGID} abc && \
    useradd -m -u ${PUID} -g ${PGID} -G audio -d /mod abc && \
    chown -R ${PUID}:${PGID} /mod

# Set MOD environment variables
ENV MOD_DEV_ENVIRONMENT=0
ENV MOD_DATA_DIR=/mod/data
ENV MOD_USER_FILES_DIR=/mod/user-files
ENV MOD_LOG=0
ENV JACK_NO_AUDIO_RESERVATION=1

# --- s6-overlay Service Definition ---
# Create the service directories
RUN mkdir -p /etc/s6/services/jackd && \
    mkdir -p /etc/s6/services/mod-ui/depends.d

# Create the jackd service script
COPY s6-services/jackd/run /etc/s6/services/jackd/run
RUN chmod +x /etc/s6/services/jackd/run

# Create the mod-ui service script
COPY s6-services/mod-ui/run /etc/s6/services/mod-ui/run
RUN chmod +x /etc/s6/services/mod-ui/run

# Create the dependency link for mod-ui
RUN ln -s /etc/s6/services/jackd /etc/s6/services/mod-ui/depends.d/jackd

# --- Final Configuration ---
# Your old entrypoint is no longer needed
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh
# CMD ["stdbuf", "-oL", "-eL", "/entrypoint.sh"]

# Set the s6-overlay entrypoint as the final command
CMD ["/init"]