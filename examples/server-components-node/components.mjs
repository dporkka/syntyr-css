// Optional copy-owned Node.js templates, not part of the Syntyr CSS runtime.
// Plain strings remain untrusted unless passed through escapeHtml before HTML insertion.
export function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

export function field({ id, name, label, value = '', help = '', error = '' }) {
  const errorId = `${id}-error`;
  const helpId = `${id}-help`;
  const describedBy = error ? errorId : help ? helpId : '';
  const attrs = [
    `class="syn-input"`, 'type="search"', `id="${escapeHtml(id)}"`,
    `name="${escapeHtml(name)}"`, `value="${escapeHtml(value)}"`,
  ];
  if (error) attrs.push('aria-invalid="true"');
  if (describedBy) attrs.push(`aria-describedby="${escapeHtml(describedBy)}"`);
  return `<div class="syn-field"${error ? ' data-syn-state="error"' : ''}>
  <label class="syn-label" for="${escapeHtml(id)}">${escapeHtml(label)}</label>
  <input ${attrs.join(' ')}>
  ${error ? `<p class="syn-error" id="${escapeHtml(errorId)}">${escapeHtml(error)}</p>` :
    help ? `<p class="syn-help" id="${escapeHtml(helpId)}">${escapeHtml(help)}</p>` : ''}
</div>`;
}

export function notice({ message, danger = false }) {
  return `<p class="syn-alert${danger ? ' syn-alert--danger' : ''}" role="${danger ? 'alert' : 'status'}">${escapeHtml(message)}</p>`;
}

export function button({ label, primary = false, submit = false }) {
  return `<button class="syn-button${primary ? ' syn-button--primary' : ''}" type="${submit ? 'submit' : 'button'}">${escapeHtml(label)}</button>`;
}

export function table(records) {
  if (records.length === 0) return '<p role="status">No matching resources.</p>';
  return `<div class="syn-table-wrap"><table class="syn-table">
  <caption>Matching resources</caption>
  <thead><tr><th scope="col">Resource</th><th scope="col">Description</th></tr></thead>
  <tbody>${records.map((record) => `<tr><th scope="row">${escapeHtml(record.title)}</th><td>${escapeHtml(record.description)}</td></tr>`).join('')}</tbody>
</table></div>`;
}

// Limit link destinations to server-generated, root-relative paths. HTML escaping
// alone does not make a javascript: or scheme-relative URL safe in href.
function safePageHref(value) {
  if (typeof value !== 'string' || !/^\/(?!\/)/.test(value) || /[\\\u0000-\u001f\u007f]/.test(value)) {
    throw new TypeError('Unsafe pagination URL');
  }
  return escapeHtml(value);
}

export function pagination({ page, total, prevURL = '', nextURL = '' }) {
  return `<nav aria-label="Resource pages" class="syn-inline">
  ${prevURL ? `<a class="syn-button" href="${safePageHref(prevURL)}" rel="prev">Previous</a>` : ''}
  <span aria-current="page">Page ${escapeHtml(page)} of ${escapeHtml(total)}</span>
  ${nextURL ? `<a class="syn-button" href="${safePageHref(nextURL)}" rel="next">Next</a>` : ''}
</nav>`;
}

export function renderPage({ query, notice: alert, searchButton, records, pager, showResults = true }) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Server HTML components — Syntyr</title>
  <link rel="stylesheet" href="/assets/syntyr.core.css">
</head>
<body class="syn-root syn-page" data-syn-theme="studio">
  <main class="syn-shell syn-stack">
    <header><h1 class="syn-heading">Syntyr Server Components</h1><p>Composable native HTML generated with Node.js.</p></header>
    ${notice(alert)}
    <form method="get" action="/" role="search" class="syn-form">
      ${field(query)}
      ${button(searchButton)}
    </form>
    ${showResults === false ? '' : `<section aria-label="Results" class="syn-stack">
      ${table(records)}
      ${pagination(pager)}
    </section>`}
    <details><summary>How this works</summary>
      <p>The server renders and escapes content, validates input, and preserves query state. Syntyr only styles native HTML.</p>
    </details>
  </main>
</body>
</html>`;
}
