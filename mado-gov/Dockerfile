# Start from a minimal base image that is good for containers
# Using a slim or alpine variant would be even better for size
FROM python:3.9-alpine

ARG TARGETARCH

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


# Install git and upgrade pip
RUN apk add --no-cache git \
    && pip install --no-cache-dir --upgrade pip


RUN pip3 install git+https://github.com/moddevices/browsepy.git backports.shutil-get-terminal-size scandir

COPY services.d/ /etc/s6-overlay/s6-rc.d/
RUN chmod +x /etc/s6-overlay/s6-rc.d/browsepy/run && \
    echo longrun > /etc/s6-overlay/s6-rc.d/browsepy/type && \
    echo browsepy > /etc/s6-overlay/s6-rc.d/user/contents.d/browsepy

CMD ["/init"]
