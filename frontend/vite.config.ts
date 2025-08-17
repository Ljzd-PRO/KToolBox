import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: '../ktoolbox/webui/static',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:8888',
      '/auth': 'http://127.0.0.1:8888',
      '/ws': {
        target: 'ws://127.0.0.1:8888',
        ws: true,
      },
    },
  },
})