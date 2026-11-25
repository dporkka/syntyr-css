import { fileURLToPath } from "node:url";

// The fixture consumes @syntyr/css and @syntyr/react through local file:
// dependencies. Next.js 16 Turbopack needs their common filesystem ancestor.
// Resolve from this file rather than the caller's working directory.
export default {
  turbopack: {
    root: fileURLToPath(new URL("../..", import.meta.url)),
  },
};
