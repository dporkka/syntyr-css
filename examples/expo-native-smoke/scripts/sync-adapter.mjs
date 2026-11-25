/** Build-local copy of the canonical, copy-owned Syntyr React Native adapter.
 * Never maintain another source of truth for the mobile palette or sample UI.
 */
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const fixture = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repo = resolve(fixture, "../..");
const outputFlag = process.argv.indexOf("--output");
if (outputFlag !== -1 && !process.argv[outputFlag + 1]) {
  throw new Error("Missing --output directory");
}
const output = outputFlag === -1 ? resolve(fixture, "src") : resolve(process.argv[outputFlag + 1]);
mkdirSync(output, { recursive: true });
for (const name of ["tokens.ts", "styles.ts"]) {
  copyFileSync(resolve(repo, "integrations/react-native", name), resolve(output, name));
}
const app = readFileSync(resolve(repo, "examples/react-native/App.tsx"), "utf8");
const oldPrefix = "../../integrations/react-native/";
if (!app.includes(oldPrefix)) throw new Error("Canonical App.tsx imports changed; update the sync contract");
writeFileSync(resolve(output, "App.tsx"), app.replaceAll(oldPrefix, "./"));
console.log("Syntyr mobile adapter synchronized from canonical source");
