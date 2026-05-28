import type { Plugin } from 'vite'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function htmlEntryPlugin(entry: string): Plugin {
  return {
    name: 'html-entry',
    transformIndexHtml(html) {
      return html.replace('/src/main.tsx', entry)
    },
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isWeb = mode === 'web'
  const isDesktop = mode === 'desktop'

  return {
    plugins: [
      react(),
      htmlEntryPlugin(isDesktop ? '/src/main.desktop.tsx' : '/src/main.web.tsx'),
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
        input: 'index.html',
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
