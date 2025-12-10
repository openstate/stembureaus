import path from "node:path";

import { defineConfig } from "vite";
import { viteStaticCopy } from 'vite-plugin-static-copy'

export default defineConfig({
  root: path.join(__dirname, "."),
  base: "/static/dist/",
  resolve: {
    alias: {
      '~bootstrap': path.resolve(__dirname, 'node_modules/bootstrap'),
    }
  },
  build: {
    outDir: path.join(__dirname, "../static/dist/"),
    manifest: "manifest.json",
    assetsDir: "bundled",
    rollupOptions: {
        input: [
          "scripts/main.js",
          "styles/main.scss",
        ],
    },
    emptyOutDir: true,
    copyPublicDir: true,
    commonjsOptions: {
      include: [/nlmaps.iife/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: ['nlmaps.iife'],
  },
  plugins: [
    viteStaticCopy({
      targets: [
        {
          src: 'node_modules/bootstrap-icons/font/fonts/*',
          dest: 'bundled/fonts',
          overwrite: true
        },
        {
          src: 'node_modules/@fortawesome/fontawesome-free/webfonts/*',
          dest: 'bundled/webfonts',
          overwrite: true
        },
      ],
    }),
  ],
});