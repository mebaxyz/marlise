FROM nginx:alpine

# Remove default static content
RUN rm -rf /usr/share/nginx/html/*

# Copy a default nginx site configuration (can be overridden at runtime via a mount)
# The file lives at docker/nginx.conf relative to the repository root build context.
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy wait-for helper and entrypoint wrapper
COPY ../scripts/wait-for.sh /usr/local/bin/wait-for.sh
RUN chmod +x /usr/local/bin/wait-for.sh

# Add entrypoint script that waits for configured targets before starting nginx
COPY docker/wait-and-start.sh /docker-entrypoint.d/wait-and-start.sh
RUN chmod +x /docker-entrypoint.d/wait-and-start.sh

# NOTE: in development the static files are mounted from the host
# via docker-compose.dev.yml. For production builds, place your
# built static files under `client-interface/web/static` before
# building the image or modify this Dockerfile to copy from the
# appropriate build output directory.

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
