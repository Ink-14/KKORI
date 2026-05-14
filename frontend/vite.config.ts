import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/raw-check': 'http://127.0.0.1:8765',
      '/nfa-check': 'http://127.0.0.1:8765',
      '/check': 'http://127.0.0.1:8765',
    }
  }
})
