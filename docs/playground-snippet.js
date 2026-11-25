/* Documentation-only copy/export logic. Never loaded by Syntyr's distributed CSS. */
(() => {
  "use strict";

  const KNOWN_MODULES = new Set([
    "syntyr.core.css",
    "syntyr.recipes.css",
    "syntyr.geometry.css",
    "syntyr.viz.css",
    "syntyr.utilities.css",
    "syntyr.semantic.css",
    "syntyr.effects.css",
    "syntyr.motion.css",
    "syntyr.symbols.css",
    "syntyr.geo.css",
    "syntyr.data-grid.css",
    "syntyr.print.css",
    "syntyr.email.css",
    "syntyr.media.css",
    "syntyr.embed.css",
    "syntyr.native-recipes.css",
    "syntyr.semantic-bundle.css",
    "syntyr.server.css"
  ]);
  const THEMES = new Set([
    "studio", "grid", "noir", "industrial", "terminal",
    "corporate", "minimal", "auto"
  ]);

  function requiredStylesheets(moduleDescription = "syntyr.core.css") {
    if (typeof moduleDescription !== "string") {
      throw new TypeError("Example stylesheet metadata must be a string");
    }
    const declared = moduleDescription.split(/\s*\+\s*/);
    if (!declared.length || declared.some(name => !KNOWN_MODULES.has(name))) {
      throw new Error("Unsupported Syntyr stylesheet in selected example");
    }
    // Every optional component uses the shared core token/root contract.
    const selected = ["syntyr.core.css"];
    for (const name of declared) {
      if (!selected.includes(name)) selected.push(name);
    }
    return selected;
  }

  function previewStylesheets(module) {
    return requiredStylesheets(module).map(
      name => `<link rel="stylesheet" href="../dist/${name}">`
    ).join("\n");
  }

  function configuredSnippet({ theme, tokens = "", module, markup = "" }) {
    if (!THEMES.has(theme)) throw new Error("Unsupported Syntyr theme");
    // Values originate from the documentation sliders, not pasted HTML.
    if (typeof tokens !== "string" || !/^[a-zA-Z0-9 ;:%.\-]*$/.test(tokens)) {
      throw new Error("Invalid playground token overrides");
    }
    if (typeof markup !== "string") throw new TypeError("Markup must be text");
    const links = requiredStylesheets(module).map(
      name => `<link rel="stylesheet" href="./${name}">`
    );
    return `<!-- Self-host these files from one pinned Syntyr release. Put links in <head>. -->\n${links.join("\n")}\n<div class="syn-root" data-syn-theme="${theme}" style="${tokens}">\n${markup}\n</div>`;
  }

  window.SYNTYR_PLAYGROUND_SNIPPET = Object.freeze({
    requiredStylesheets,
    previewStylesheets,
    configuredSnippet
  });
})();
