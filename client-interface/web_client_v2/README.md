Marlise web client v2 (prototype)

Run locally:

1. cd client-interface/web_client_v2
2. npm install
3. npm run dev

The dev server proxies /api and /ws to the running backend on localhost:8080 and listens
by default on http://localhost:5173. If that port is already in use Vite will select the
next available port (for example 5174).
