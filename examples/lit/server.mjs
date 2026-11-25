// Test-only static fixture server. No app network dependency or framework API.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };
createServer(async (req, res) => {
  const pathname = new URL(req.url, "http://localhost").pathname;
  if (!["/dist/", "/examples/lit/", "/examples/web-components/"].some(prefix => pathname.startsWith(prefix))) {
    res.writeHead(404); res.end(); return;
  }
  const file = resolve(root, "." + pathname);
  if (!file.startsWith(root + sep) || !types[extname(file)]) {
    res.writeHead(404); res.end(); return;
  }
  try {
    const data = await readFile(file);
    res.writeHead(200, { "Content-Type": types[extname(file)], "X-Content-Type-Options": "nosniff" });
    res.end(data);
  } catch {
    res.writeHead(404); res.end();
  }
}).listen(4188, "127.0.0.1");
