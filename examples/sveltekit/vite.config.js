import adapter from '@sveltejs/adapter-auto';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// The SvelteKit host handles routing, server actions, and hydration.
// Syntyr remains an imported, framework-neutral stylesheet.
export default defineConfig({ plugins: [sveltekit({ adapter: adapter() })] });
