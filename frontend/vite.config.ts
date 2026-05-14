import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isProd = process.env.NODE_ENV === 'production'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: isProd ? '/korean_spell_checker/' : '/',
  define: {
    __API_BASE__: isProd
      ? JSON.stringify('https://koreanspellchecker-production.up.railway.app')
      : JSON.stringify(''),
  },
  server: {
    proxy: {
      '/raw-check': 'http://127.0.0.1:8765',
      '/nfa-check': 'http://127.0.0.1:8765',
      '/check': 'http://127.0.0.1:8765',
    }
  }
})
