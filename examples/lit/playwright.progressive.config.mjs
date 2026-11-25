import { defineConfig } from "@playwright/test";

// This CI-only suite uses browser automation but runs the Syntyr pages with
// application JavaScript disabled. The GET endpoint is the actual Python
// standard-library fixture shared with the other progressive browser tests.
export default defineConfig({
  testDir: "./progressive-tests",
  testMatch: "progressive.spec.mjs",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  timeout: 20_000,
  use: {
    javaScriptEnabled: false,
    reducedMotion: "reduce",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
    { name: "firefox", use: { browserName: "firefox" } },
    { name: "webkit", use: { browserName: "webkit" } },
  ],
  webServer: {
    command: "python3 ../../examples/htmx_server.py",
    url: "http://127.0.0.1:8765/examples/htmx.html",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
