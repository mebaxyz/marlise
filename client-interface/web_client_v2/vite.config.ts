import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Lock the dev server to the common Vite default port so the
    // local docs and README can assume a stable URL. Vite will still
    // pick a different port if 5173 is in use.
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8080',
      // forward the lightweight health endpoint as well
      '/api/health': 'http://localhost:8080',
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true
      },
      '/snapshot': 'http://localhost:8080'
    }
  }
})
