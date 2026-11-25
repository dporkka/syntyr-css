/**
 * Docs-only first-use assistant. Generates copy-owned HTML without adding
 * a runtime to the Syntyr CSS consumer or consulting a remote service.
 */
const labels = Object.freeze({
  saas: { title: 'SaaS dashboard', intro: 'A clear starting point for your workspace.' },
  business: { title: 'Business website', intro: 'Help visitors understand what you offer.' },
  admin: { title: 'Operations console', intro: 'Prioritize the work that matters.' },
});
const themes = ['studio', 'grid', 'noir'];
const stacks = ['html', 'go', 'react', 'django', 'htmx'];
const cssRelease = 'https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css';

export function createPlaygroundHandoff({ kind, theme, stack }) {
  // Only a bounded allowlist of identifiers crosses the URL. Never put HTML,
  // private source or arbitrary user content in history/query parameters.
  if (!Object.hasOwn(labels, kind) || !themes.includes(theme) || !stacks.includes(stack)) {
    throw new RangeError('Unsupported starter selection');
  }
  return 'playground.html#' + new URLSearchParams({ starter: kind, theme, stack }).toString();
}

export function createStarter({ kind, theme, stack }) {
  if (!Object.hasOwn(labels, kind) || !themes.includes(theme) || !stacks.includes(stack)) {
    throw new RangeError('Unsupported starter selection');
  }
  const label = labels[kind];
  const body = kind === 'business'
    ? `<header class="syn-panel"><strong>Your organization</strong></header>
    <main id="main"><section class="syn-panel" aria-labelledby="heading">
      <h1 id="heading">${label.title}</h1><p>${label.intro}</p>
      <a class="syn-button syn-button--primary" href="#contact">Contact us</a>
    </section><section class="syn-panel" id="contact" aria-labelledby="contact-heading">
      <h2 id="contact-heading">Contact</h2><p>Replace this sample with your real contact information.</p>
    </section></main>`
    : kind === 'admin'
      ? `<header class="syn-panel"><h1>${label.title}</h1>
      <nav aria-label="Application sections"><a href="#overview">Overview</a> · <a href="#tasks">Tasks</a></nav></header>
      <main id="main"><section id="overview" class="syn-panel" aria-labelledby="overview-heading">
        <h2 id="overview-heading">Overview</h2><p>${label.intro}</p>
      </section><section id="tasks" class="syn-panel" aria-labelledby="tasks-heading">
        <h2 id="tasks-heading">Tasks</h2><p>No tasks yet. Connect an authorized backend before enabling actions.</p>
      </section></main>`
      : `<header class="syn-panel"><h1>${label.title}</h1></header>
      <main id="main"><section class="syn-panel" aria-labelledby="overview-heading">
        <h2 id="overview-heading">Overview</h2><p>${label.intro}</p>
        <a class="syn-button syn-button--primary" href="#next-step">Next step</a>
      </section><section id="next-step" class="syn-panel" aria-labelledby="next-heading">
        <h2 id="next-heading">Connect your data</h2>
        <p>Replace fictional content with authorized application data.</p>
      </section></main>`;
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${label.title} — Syntyr starter</title>
  <link rel="stylesheet" href="./syntyr.core.css">
</head>
<body class="syn-root syn-shell" data-syn-theme="${theme}">
  <a href="#main" class="syn-button">Skip to content</a>
  ${body}
</body>
</html>
`;
  const integration = stack === 'go'
    ? 'Go: use html/template with automatic escaping, insert this markup in a template, and serve the pinned local CSS.'
    : stack === 'react'
      ? 'React: translate class to className and HTML attributes to JSX; import or serve the pinned local CSS. React supplies events, data and routing.'
      : stack === 'django'
        ? 'Django: put the pinned CSS in staticfiles (for example static/css/syntyr.core.css), load the static template tag, and use the static URL in your base template. Keep automatic escaping and CSRF protection for real POST forms.'
        : stack === 'htmx'
          ? 'HTMX: serve the pinned stylesheet in the persistent page shell. Begin with ordinary GET forms and links; progressively enhance with your own pinned HTMX script and return escaped fragments for HTMX requests, full documents for direct navigation.'
          : 'Plain HTML: save this output as index.html and serve it alongside the pinned local stylesheet.';
  return {
    html,
    fragment: body,
    instructions: `Published alpha.4 (v0.3.0-alpha.4). Download ${cssRelease} and self-host it as syntyr.core.css next to index.html. ${integration} This starter is static: add authentication, backend actions, validation and access control in your host application.`,
  };
}

if (typeof document !== 'undefined') {
  const form = document.getElementById('starter-form');
  const result = document.getElementById('starter-result');
  const output = document.getElementById('starter-code');
  const help = document.getElementById('starter-instructions');
  const copy = document.getElementById('starter-copy');
  const status = document.getElementById('starter-status');
  const edit = document.getElementById('starter-edit');
  if (form && result && output && help && copy && status) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      try {
        const starter = createStarter({
          kind: form.elements.namedItem('kind').value,
          theme: form.elements.namedItem('theme').value,
          stack: form.elements.namedItem('stack').value,
        });
        output.value = starter.html;
        help.textContent = starter.instructions;
        result.hidden = false;
        copy.disabled = false;
        if (edit) edit.href = createPlaygroundHandoff({
          kind: form.elements.namedItem('kind').value,
          theme: form.elements.namedItem('theme').value,
          stack: form.elements.namedItem('stack').value,
        });
        status.textContent = 'Starter generated locally. Review the HTML and integration notes.';
      } catch {
        status.textContent = 'Select a supported project, theme and integration.';
      }
    });
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(output.value);
        status.textContent = 'Starter HTML copied to clipboard.';
      } catch {
        output.focus();
        output.select();
        status.textContent = 'Clipboard unavailable. HTML selected for manual copying.';
      }
    });
  }
}
