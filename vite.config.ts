/// <reference types="vitest/config" />
// defineConfig comes from vite; vitest/config augments it with the `test` block.
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

// The frontend only needs one setting: where the API lives.
// Production (Vercel): set VITE_API_URL to the deployed FastAPI base URL.
// Development: /api is proxied to the local backend on port 8000.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = Number(env.VITE_BACKEND_PORT || 8000);
  const backendHost = env.VITE_BACKEND_HOST || 'localhost';
  const target = `http://${backendHost}:${backendPort}`;

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          secure: false,
          configure: (proxy) => {
            proxy.on('error', (err) => {
              console.error(`[proxy] ${err.message} - is the API running on ${target}?`);
            });
          },
        },
      },
    },
    preview: {
      port: 4173,
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1200,
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
    },
  };
});
