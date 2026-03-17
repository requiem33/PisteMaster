import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': resolve('src/main'),
      },
    },
    build: {
      rollupOptions: {
        external: ['electron'],
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': resolve('src/preload'),
      },
    },
    build: {
      rollupOptions: {
        external: ['electron'],
      },
    },
  },
  renderer: {
    root: resolve(__dirname, '../web_frontend'),
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, '../web_frontend/index.html'),
        },
      },
    },
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, '../web_frontend/src'),
      },
    },
    server: {
      port: 3001,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  },
})