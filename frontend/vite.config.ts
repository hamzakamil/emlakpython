import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@views': path.resolve(__dirname, './src/views'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@layouts': path.resolve(__dirname, './src/layouts'),
      '@router': path.resolve(__dirname, './src/router'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Backend yolları "api/v1/..." biçiminde; önek dönüştürülmez
      // (önceki rewrite /api önekini siliyordu — backend'e uymuyordu, düzeltildi).
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
  },
  build: {
    outDir: 'dist',
    // FAZ 6F-4: prod sourcemap kapalı (kaynak ifşası yok).
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          query: ['@tanstack/vue-query'],
          ui: ['lucide-vue-next', '@headlessui/vue', '@heroicons/vue'],
          charts: ['chart.js', 'vue-chartjs'],
          table: ['@tanstack/vue-table'],
          forms: ['vee-validate', 'zod', '@vee-validate/zod'],
          utils: ['date-fns', 'clsx', 'tailwind-merge', '@vueuse/core'],
          export: ['xlsx', 'pdfmake', 'jspdf', 'jspdf-autotable'],
          editor: ['quill', '@tiptap/vue-3', '@tiptap/starter-kit'],
        },
      },
    },
  },
})