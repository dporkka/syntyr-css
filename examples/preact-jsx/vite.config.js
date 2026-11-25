import { defineConfig } from "vite";

export default defineConfig({
  // Use Preact's JSX runtime, not React or a Syntyr-specific compiler.
  esbuild: { jsx: "automatic", jsxImportSource: "preact" },
});
