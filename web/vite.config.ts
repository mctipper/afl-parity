import { fileURLToPath, URL } from 'node:url'
import { defineConfig, type Plugin } from 'vite'

// Hacky way to get dev middleware to dynamically route year-shaped requests to season.html to mirror post-build production
function seasonPageDevMiddleware(): Plugin {
  return {
    name: 'season-page-dev-middleware',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const pathname = (req.url ?? '').split('?')[0]
        if (/^\/afl-parity\/\d{4}\/?$/.test(pathname)) {
          req.url = '/afl-parity/season.html'
        }
        next()
      })
    },
  }
}

export default defineConfig({
  base: '/afl-parity/',
  plugins: [seasonPageDevMiddleware()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 1897,
  },
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        season: fileURLToPath(new URL('./season.html', import.meta.url)),
      },
    },
  },
})
