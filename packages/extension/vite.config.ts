import { defineConfig } from 'vite';
import { resolve } from 'path';
import { copyFileSync, mkdirSync, existsSync } from 'fs';

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        'background/service-worker': resolve(__dirname, 'src/background/service-worker.ts'),
        'content/selection': resolve(__dirname, 'src/content/selection.ts'),
        'popup/popup': resolve(__dirname, 'src/popup/popup.ts'),
        'sidepanel/panel': resolve(__dirname, 'src/sidepanel/panel.ts'),
        'options/options': resolve(__dirname, 'src/options/options.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
    target: 'esnext',
    minify: false,
  },
  plugins: [
    {
      name: 'copy-extension-files',
      closeBundle() {
        const distDir = resolve(__dirname, 'dist');
        const srcDir = resolve(__dirname, 'src');
        const publicDir = resolve(__dirname, 'public');
        ['popup', 'sidepanel', 'options'].forEach((dir) => {
          const outDir = resolve(distDir, dir);
          if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
          copyFileSync(resolve(srcDir, dir, 'index.html'), resolve(outDir, 'index.html'));
        });
        copyFileSync(resolve(publicDir, 'manifest.json'), resolve(distDir, 'manifest.json'));
        const iconsDir = resolve(distDir, 'icons');
        if (!existsSync(iconsDir)) mkdirSync(iconsDir, { recursive: true });
        ['icon16.svg', 'icon48.svg', 'icon128.svg'].forEach((icon) => {
          copyFileSync(resolve(publicDir, 'icons', icon), resolve(iconsDir, icon));
        });
      },
    },
  ],
});
