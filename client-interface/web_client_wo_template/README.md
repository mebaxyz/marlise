This directory is a copy of the original `client-interface/web_client/static` folder but without the template wrapper.

It is used by development tooling and docker-compose to serve static assets when developing without the template.

If you need to refresh the contents, copy from `client-interface/web_client/static` or regenerate them from the frontend build. For development the compose file now mounts `client-interface/web_client_wo_template/static`.
