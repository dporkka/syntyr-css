import { defineConfig } from "vite";
import solid from "vite-plugin-solid";

// Solid owns JSX transformation and reactive behavior; Syntyr remains CSS.
export default defineConfig({ plugins: [solid()] });
