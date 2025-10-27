import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy all API calls to the backend during development
      '/api': 'http://localhost:5656',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
