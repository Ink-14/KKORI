import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isWeb = mode === 'web'
  const isDesktop = mode === 'desktop'

  return {
    plugins: [
      react(),
    ],
    base: isWeb ? '/korean_spell_checker/' : '/',
    define: {
      __API_BASE__: isWeb
        ? JSON.stringify('https://koreanspellchecker-production.up.railway.app')
        : JSON.stringify(''),
    },
    build: {
      outDir: isWeb ? 'dist/web' : 'dist/desktop',
      rollupOptions: {
        input: isDesktop ? 'index.desktop.html' : 'index.web.html',
      }
    },
    server: {
      proxy: {
        '/raw-check': 'http://127.0.0.1:8765',
        '/nfa-check': 'http://127.0.0.1:8765',
        '/check': 'http://127.0.0.1:8765',
        '/add-words': 'http://127.0.0.1:8765',
        '/words': 'http://127.0.0.1:8765',
      }
    }
  }
})
