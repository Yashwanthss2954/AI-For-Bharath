import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all addresses including LAN
    allowedHosts: [
      'cartridges-kits-included-strengthening.trycloudflare.com',
      '.trycloudflare.com', // Allow all cloudflare tunnel subdomains
      'localhost',
      'ai-for-bharath-1.onrender.com'
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
