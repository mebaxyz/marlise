#!/bin/bash
set -e

# Use default values if not set
PUID=${PUID:-1000}
PGID=${PGID:-1000}


cd /mod/mod-plugin-builder


# gosu "${PUID}" ./bootstrap.sh generic-aarch64

for i in $(ls plugins/package | egrep -v 'max-gen|fluidplug|zynaddsubfx|pdlv2-labs|zeroconvo'); do
    gosu "${PUID}" ./build generic-aarch64 "$i"
done

cp -rfp mod-workdir/generic-aarch64/plugins/* /mod/plugins

bash /mod/mod-plugin-builder/copy_modguis.sh

echo "✅ Build complete. Container will remain active..."

# Keep container alive
exec bash
