import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [
    react(),
    dts({
      include: ['src'],
      outDir: 'dist',
      rollupTypes: true,
    }),
  ],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'ConversationalBIWidget',
      formats: ['es', 'cjs'],
      fileName: (format) =>
        format === 'es' ? 'conversational-bi-widget.mjs' : 'conversational-bi-widget.cjs',
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime'],
      output: {
        assetFileNames: 'conversational-bi-widget.[ext]',
      },
    },
    cssCodeSplit: false,
  },
})
