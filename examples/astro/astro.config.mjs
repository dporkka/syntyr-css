import { defineConfig } from 'astro/config';

// Exercise a project-subdirectory deployment, not just a root-path build.
export default defineConfig({
  output: 'static',
  base: '/syntyr-astro/',
});
