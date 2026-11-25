import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import keystatic from '@keystatic/astro';

// Editorial routes exist only during explicitly opted-in local development.
// The production export has no CMS API endpoint or editor JavaScript.
const localEditor = process.env.SYNTYR_ENABLE_LOCAL_EDITOR === '1'
  && process.env.NODE_ENV === 'development';

export default defineConfig({
  output: 'static',
  base: '/syntyr-astro-keystatic/',
  server: { host: '127.0.0.1' },
  integrations: localEditor ? [react(), keystatic()] : [],
});
