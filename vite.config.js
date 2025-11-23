import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      devOptions: {
        enabled: true,
      },
      manifest: {
        name: 'Nexus OS',
        short_name: 'Nexus',
        description: 'Next-gen personal finance, trading, and wallet ecosystem.',
        theme_color: '#0B0E11',
        background_color: '#0B0E11',
        display: 'standalone',
        icons: [
          {
            src: '/logo.jpg',
            sizes: '192x192',
            type: 'image/jpeg',
          },
          {
            src: '/logo.jpg',
            sizes: '512x512',
            type: 'image/jpeg',
          },
          {
            src: '/logo.jpg',
            sizes: '512x512',
            type: 'image/jpeg',
            purpose: 'maskable',
          },
        ],
      },
    }),
  ],
  server: {
    host: true, // Allow access from external devices
    port: 3000, // Default port
  },
  build: {
    outDir: 'dist',
    sourcemap: true, // Generate source maps for debugging
  },
});
