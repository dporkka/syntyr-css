/** Optional Syntyr + Eleventy example; CSS always comes from this repo's dist. */
import { execFileSync } from "node:child_process";

const pathPrefix = "/syntyr-eleventy/";

export default function (eleventyConfig) {
  // Validate the existing CMS contract before the template sees the data.
  const page = JSON.parse(execFileSync("python3", [
    "-c",
    "import json; from scripts.render_cms_starter import validate_document, STARTER; page = json.loads((STARTER / 'content/pages/home.json').read_text()); validate_document(page); print(json.dumps(page))",
  ], { cwd: new URL("../..", import.meta.url), encoding: "utf8" }));
  eleventyConfig.addGlobalData("pageContent", page);
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
