import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sisuLocalDevDbPlugin } from './scripts/local-dev-db.mjs'

export default defineConfig(({ command }) => ({
  plugins: [vue(), ...(command === 'serve' && process.env.SISU_USE_REMOTE !== '1' ? [sisuLocalDevDbPlugin()] : [])],
  base: command === 'build' ? '/assets/institute_lms/portal/' : '/',
  build: { outDir: '../institute_lms/public/portal', emptyOutDir: true },
  server: {
    port: 5178,
    strictPort: true,
    // Set SISU_USE_REMOTE=1 and SISU_FRAPPE_URL to proxy to a remote Frappe site instead of the local dev DB.
    proxy: process.env.SISU_USE_REMOTE === '1' && process.env.SISU_FRAPPE_URL ? Object.fromEntries(['/api','/login','/me','/files','/private','/assets/frappe'].map(path=>[path,{target:process.env.SISU_FRAPPE_URL,changeOrigin:true,followRedirects:true,secure:false}])) : undefined
  },
}))
