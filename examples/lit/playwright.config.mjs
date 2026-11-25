import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  timeout: 15_000,
  use: {
    baseURL: "http://127.0.0.1:4188",
    reducedMotion: "reduce",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
    { name: "firefox", use: { browserName: "firefox" } },
    { name: "webkit", use: { browserName: "webkit" } },
  ],
  webServer: {
    command: "node server.mjs",
    url: "http://127.0.0.1:4188/examples/lit/index.html",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
