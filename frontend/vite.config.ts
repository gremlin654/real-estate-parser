import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import istanbul from 'vite-plugin-istanbul'
import path from 'path'

// GitHub Pages base - установить через env или по умолчанию
const base = process.env.VITE_BASE_URL || '/'

export default defineConfig({
  base,
  plugins: [
    react(),
    istanbul({
      include: ['src/**/*'],
      exclude: ['node_modules', 'tests/', '**/*.d.ts'],
      requireEnv: false,
      forceBuildInstrument: true,
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
