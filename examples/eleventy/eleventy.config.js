/** Optional Syntyr + Eleventy example; CSS always comes from this repo's dist. */
export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({
    "../../dist/syntyr.core.css": "assets/syntyr.core.css",
  });

  return {
    dir: { input: "src", output: "_site" },
    // Exercise GitHub Pages/project subpaths, not just root deployments.
    pathPrefix: "/syntyr-eleventy/",
  };
}
