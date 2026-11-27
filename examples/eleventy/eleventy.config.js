/** Optional Syntyr + Eleventy example; CSS always comes from this repo's dist. */
import { execFileSync } from "node:child_process";

const pathPrefix = "/syntyr-eleventy/";

export default function (eleventyConfig) {
  // Reject ambiguous JSON at the canonical input boundary before templating.
  // The transport cap accommodates the entire bounded UTF-8 source document,
  // not just Node's default 1 MiB stdout buffer.
  const loadPage = () => JSON.parse(execFileSync("python3", [
    "-c",
    `import json, sys
from scripts.render_cms_starter import load_validated_document, STARTER
page = load_validated_document(STARTER / "content/pages/home.json")
sys.stdout.buffer.write(json.dumps(page, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8"))`,
  ], { cwd: new URL("../..", import.meta.url), encoding: "utf8", maxBuffer: 16 * 1024 * 1024 }));
  // Load on every build: Eleventy may remap out-of-tree watch paths, so
  // config reset alone does not reliably refresh external template data.
  eleventyConfig.addWatchTarget("../cms-starter/content/pages/home.json", { resetConfig: true });
  eleventyConfig.addGlobalData("pageContent", loadPage);
  eleventyConfig.setNunjucksEnvironmentOptions({ autoescape: true });
  eleventyConfig.addFilter("cmsUrl", value => value.startsWith("/") ? pathPrefix + value.slice(1) : value);
  eleventyConfig.addPassthroughCopy({
    "../../dist/syntyr.core.css": "assets/syntyr.core.css",
    "../../dist/syntyr.recipes.css": "assets/syntyr.recipes.css",
  });

  return {
    dir: { input: "src", output: "_site" },
    // Exercise GitHub Pages/project subpaths, not just root deployments.
    pathPrefix,
  };
}
