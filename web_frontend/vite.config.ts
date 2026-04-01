/// <reference types="vitest" />
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import {resolve} from 'path'

export default defineConfig({
    base: './',
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src')
        }
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    },
    test: {
        environment: 'jsdom',
        globals: true,
        include: ['src/**/*.{test,spec}.{js,ts}'],
        setupFiles: ['./src/test-utils/setup.ts'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html'],
            exclude: [
                'node_modules/',
                'src/**/*.d.ts',
                'src/**/*.config.*',
                'src/main.ts',
                'src/test-utils/**',
            ],
            all: true,
        },
    },
})