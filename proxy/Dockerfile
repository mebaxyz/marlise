# Use Alpine-based Nginx image
FROM nginx:alpine

# Copy your custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Optional: Add static error pages or assets
# COPY ./static /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
