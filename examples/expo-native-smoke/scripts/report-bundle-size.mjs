/** Compare local, same-screen Expo production JS/Hermes exports.
 * Counts raw bundle bytes, not startup time, native binary size, or frame timing.
 */
import { readdirSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";

const [platform, ...specs] = process.argv.slice(2);
if (!["android", "ios"].includes(platform) || specs.length < 1) {
  console.error("Usage: node scripts/report-bundle-size.mjs <android|ios> <label=export-dir> [...]");
  process.exit(2);
}

function measure(spec) {
  const separator = spec.indexOf("=");
  const label = spec.slice(0, separator);
  const path = spec.slice(separator + 1);
  if (separator < 1 || !path || !/^[A-Za-z0-9_-]+$/.test(label)) throw new Error("Expected label=export-dir");
  const dir = join(path, "_expo", "static", "js", platform);
  const files = readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && /\.(?:hbc|js)$/.test(entry.name))
    .map((entry) => entry.name)
    .sort()
    .map((name) => {
      const data = readFileSync(join(dir, name));
      return { name, bytes: data.length, sha256: createHash("sha256").update(data).digest("hex") };
    });
  if (files.length === 0) throw new Error(`No JS/Hermes bundles in ${dir}`);
  const formats = [...new Set(files.map((file) => file.name.endsWith(".hbc") ? "hermes" : "javascript"))];
  if (formats.length !== 1) throw new Error(`Mixed bundle formats in ${dir}`);
  return { label, format: formats[0], bytes: files.reduce((total, file) => total + file.bytes, 0), files };
}

try {
  const cases = specs.map(measure);
  if (new Set(cases.map(({ label }) => label)).size !== cases.length) throw new Error("Labels must be unique");
  const baseline = cases[0];
  if (baseline.bytes === 0) throw new Error("Baseline bundle is empty");
  if (cases.some(({ format }) => format !== baseline.format)) throw new Error("Compare the same bundle format");
  console.log(JSON.stringify({
    platform,
    metric: "raw-production-js-bundle-bytes",
    baseline: baseline.label,
    cases: cases.map((entry) => ({
      ...entry,
      deltaBytes: entry.bytes - baseline.bytes,
      deltaPercent: Number(((entry.bytes / baseline.bytes - 1) * 100).toFixed(2)),
    })),
  }, null, 2));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
