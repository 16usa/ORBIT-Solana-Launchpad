import { defineConfig } from 'vite';
export default defineConfig({
  root: 'web',
  envDir: '..',
  publicDir: 'public',
  build: { outDir: '../dist', emptyOutDir: true, target: 'es2022' },
  optimizeDeps: { esbuildOptions: { target: 'es2022' } },
  define: { 'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV ?? 'development') },
  server: {
    host: '0.0.0.0',
    port: Number(process.env.PORT || 5173),
    strictPort: true,
    allowedHosts: true,
    proxy: Object.fromEntries(['/api', '/media', '/metadata'].map(route => [route, { target: `http://127.0.0.1:${process.env.API_PORT || '8080'}`, changeOrigin: true }])),
  },
});
