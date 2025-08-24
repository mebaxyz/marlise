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


ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
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


# Install OpenSSH, pip, and BrowsePy using apt
RUN apt-get update && \
    apt-get install -y openssh-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set root password
RUN echo "root:root" | chpasswd

# Configure SSH
RUN sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    mkdir -p /var/run/sshd

# Expose ports for SSH and BrowsePy
EXPOSE 22 8081

RUN pip3 install browsepy

# Create s6 service directories
COPY ./services.d /etc/s6/services.d 
RUN chmod +x /etc/s6/services.d/browsepy/run && \
    chmod +x /etc/s6/services.d/sshd/run

# Define the directory for BrowsePy
ENV BROWSEPY_DIR=/mod-data

CMD ["/init"]
# The base image's entrypoint will start s6, which will run the services.d scripts.