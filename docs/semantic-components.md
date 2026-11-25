# Semantic HTML component recipes

Build article previews, breadcrumbs, citations, metadata lists, change histories,
internationalized labels, tables, FAQs, search forms, measured status, and
responsive media with **native HTML**. Syntyr styles
these elements without replacing browser semantics or adding a JavaScript runtime.
These are copy-owned markup compositions in the free MIT core—not new JS widgets.

[View the live semantic component gallery](../examples/semantic-compositions.html).
For the existing forms, dialogs, search and disclosure patterns, see
[native platform patterns](native-patterns.md).

## Install semantic styling

Load core first, semantic second. Both are plain CSS; styles apply only to a
`.syn-root.syn-semantic` element or a `.syn-semantic` subtree inside
`.syn-root`. Classless elements are styled automatically. Add
`data-syn-semantic` to classed elements **only** when opting them into the
semantic rules. A classed element keeps its explicitly chosen component styles.

~~~html
<link rel="stylesheet" href="/dist/syntyr.core.css">
<link rel="stylesheet" href="/dist/syntyr.semantic.css">
<main class="syn-root syn-semantic" data-syn-theme="studio">
  <article><h1>Semantic HTML, styled by Syntyr</h1></article>
</main>
~~~

Use version-pinned stylesheets from your own deployment in production. These
examples require **no JavaScript**. Any data lookup, routing, persistence or
change handling still belongs to the server or host application.

## Article preview with publication date

Use `article` for a self-contained work and `time[datetime]` for
machine-readable dates. Avoid `article` merely to get a bordered card:
use `.syn-panel` on an ordinary container instead.

~~~html
<article>
  <header>
    <h2><a href="/notes/semantic-html">Semantic HTML in practice</a></h2>
    <p>Published <time datetime="2026-11-16">16 November 2026</time></p>
  </header>
  <p>A compact guide to meaningful browser-native markup.</p>
  <footer><small>Documentation team</small></footer>
</article>
~~~

## Breadcrumb navigation

Use a real `nav` landmark, an ordered list and `aria-current="page"`.
Syntyr already provides `.syn-breadcrumbs`; do not create a second breadcrumb
component or hand-code presentational separator characters.

~~~html
<nav class="syn-breadcrumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/docs">Docs</a></li>
    <li aria-current="page">Semantics</li>
  </ol>
</nav>
~~~

## Definitions and structured metadata

Use `dl`, `dt`, and `dd` for name/value pairs; `data[value]` for a
machine-readable value, `abbr[title]` for a genuine abbreviation, and
`time[datetime]` for dates. Do not use `dl` merely as a two-column grid.

~~~html
<dl>
  <dt>Plan</dt><dd>Team</dd>
  <dt>Seats</dt><dd><data value="12">12 active seats</data></dd>
  <dt>Renewal</dt><dd><time datetime="2027-01-01">1 January 2027</time></dd>
  <dt>Availability</dt><dd><abbr title="Service-level agreement">SLA</abbr> 99.9%</dd>
</dl>
~~~

## Quotation and source attribution

Use `blockquote` for a long quotation and a `figure` with
`figcaption` for its attribution. `cite` names the *work*, not its author;
do not manufacture a URL for the `blockquote[cite]` attribute.

~~~html
<figure>
  <blockquote><p>Use the language of the platform before adding an abstraction.</p></blockquote>
  <figcaption>From <cite>Semantic Design Notes</cite></figcaption>
</figure>
~~~

A `blockquote` may alternatively include a `footer` for supporting
attribution text. The optional semantic stylesheet styles that footer, without
changing the surrounding `footer` elements elsewhere on the page.

## Document revisions

The `ins` and `del` elements communicate additions and removals. Include a
valid `datetime` if the modification date is known. For live collaborative
editing or audit history, the server remains authoritative.

~~~html
<p>Retention: <del datetime="2026-11-15">90 days</del>
  <ins datetime="2026-11-16">120 days</ins>.</p>
~~~

## Multilingual pronunciation and bidi isolation

Use `ruby` and `rt` for pronunciation annotations; `rp` supplies text
fallback in browsers without ruby presentation. Syntyr deliberately does not restyle the
annotation; the browser owns ruby positioning, text size, and fallback. Use `bdi` for a
user-supplied string with unknown direction; `bdo` intentionally overrides
direction and should be used only when that behavior is required.

~~~html
<p>Character: <ruby>漢<rp>(</rp><rt>hàn</rt><rp>)</rp></ruby></p>
<p>Author: <bdi>مريم</bdi> — saved successfully.</p>
<p>Deliberate reverse sequence: <bdo dir="rtl">ABC</bdo></p>
~~~

## Tabular totals with a real footer

Keep a caption, column headers with `scope="col"`, row headers with
`scope="row"`, and a `tfoot` summary. The browser owns table semantics;
Syntyr's optional `tfoot` styling adds only a separator and weight. For
complex tables, connect headers using `id` and `headers` as needed.

~~~html
<table>
  <caption>Monthly license usage</caption>
  <thead><tr><th scope="col">License</th><th scope="col">Seats</th></tr></thead>
  <tbody>
    <tr><th scope="row">Team</th><td>12</td></tr>
    <tr><th scope="row">Guest</th><td>3</td></tr>
  </tbody>
  <tfoot><tr><th scope="row">Total</th><td>15</td></tr></tfoot>
</table>
~~~

## Complementary content

A contextual `aside` is a complementary landmark, not a generic card. Apply
the existing `.syn-panel` class when a visual callout is desirable.

~~~html
<aside class="syn-panel" aria-labelledby="help-title">
  <h2 id="help-title">Implementation guidance</h2>
  <p>Keep routing, translations, and data validation in the host application.</p>
</aside>
~~~

## In-page navigation

A `nav` landmark with an accessible name and a real ordered list doubles as
an in-page table of contents. Anchor destinations must exist. Do not substitute
a fake tab interface or JavaScript scrolling for ordinary document navigation.

~~~html
<nav aria-label="On this page">
  <ol>
    <li><a href="#offer">Current offer</a></li>
    <li><a href="#notes">Reference notes</a></li>
  </ol>
</nav>
<section id="offer" aria-labelledby="offer-heading">
  <h2 id="offer-heading">Current offer</h2>
  <p>Native content, no client-side routing required.</p>
</section>
<section id="notes" aria-labelledby="notes-heading">
  <h2 id="notes-heading">Reference notes</h2>
  <p>Each anchor points to a real heading section.</p>
</section>
~~~

## Previous price versus revision

Use `s` for content that is no longer accurate or relevant, such as a
superseded advertised price; `del` and `ins` instead describe **actual
document edits**. Use `data[value]` when the application needs a
machine-readable number, not to indicate currency on its own. Provide the
currency and billing period in visible text. Price, stock and promotion
eligibility must still be verified by the server before any transaction.

~~~html
<article>
  <h2>Team plan (example only)</h2>
  <p>Example price:
    <s><data value="39">US$39 per month</data></s>
    <strong><data value="29">US$29 per month</data></strong>
  </p>
  <p><small>Illustrative pricing, not a live Syntyr offer.</small></p>
</article>
~~~

Syntyr's optional semantic layer lightly de-emphasizes `s` but keeps its
native strikethrough. This rule remains scoped to classless or explicitly
opted-in elements inside `.syn-semantic`.

## Footnotes and return links

Use a normal `sup` with an anchor to a numbered `ol`, then include a
return link to the reference. This approach works with keyboard navigation,
screen readers, server-rendered HTML and no custom event handlers. Do not
put footnote bodies in an inaccessible hover-only tooltip.

~~~html
<p>Native links are keyboard accessible
  <sup id="note-ref-1"><a href="#note-1" aria-label="Footnote 1">1</a></sup>.
</p>
<section aria-labelledby="footnotes-title">
  <h2 id="footnotes-title">Notes</h2>
  <ol>
    <li id="note-1">A normal anchor connects the note and reference.
      <a href="#note-ref-1">Return to reference 1</a>
    </li>
  </ol>
</section>
~~~

Both IDs must be unique to the page, and links must resolve when fragments
are loaded directly. Keep the note text in the document, not generated solely
with CSS `content`.

## Technical notation and long identifiers

Prefer the HTML elements that convey meaning: `var` names a variable,
`samp` names program output, `kbd` represents keyboard input,
`sub` and `sup` retain native baseline notation, and `wbr` allows
line breaks within long identifiers. Syntyr deliberately leaves `sub`,
`sup` and `wbr` layout to the browser.

~~~html
<p>Area = <var>width</var> × <var>height</var>.
  Water is H<sub>2</sub>O; the formula is E = mc<sup>2</sup>.
</p>
<p>Press <kbd>Enter</kbd>. The program prints <samp>Ready</samp>.</p>
<p>Example endpoint: <code>api.example.test/<wbr>v1/<wbr>document-exports</code></p>
~~~

The domain and endpoint above are placeholders only, not production services.

## Grouped table headings

Use `colgroup` with a real `th scope="colgroup"` and subcolumn headings.
For simple tables, use `scope="col"` and `scope="row"` instead. Syntyr
already provides native cell borders and table captions; the optional
semantic styling adds a subtle `thead` background and preserves
high-contrast borders. It does not replace table accessibility semantics.

~~~html
<table>
  <caption>Example monthly accounts</caption>
  <colgroup><col></colgroup>
  <colgroup span="2"></colgroup>
  <thead>
    <tr><th scope="col" rowspan="2">Plan</th>
        <th scope="colgroup" colspan="2">Accounts</th></tr>
    <tr><th scope="col">Paid</th><th scope="col">Trial</th></tr>
  </thead>
  <tbody>
    <tr><th scope="row">Starter</th><td>8</td><td>3</td></tr>
    <tr><th scope="row">Growth</th><td>4</td><td>2</td></tr>
  </tbody>
  <tfoot><tr><th scope="row">Total</th><td>12</td><td>5</td></tr></tfoot>
</table>
~~~

## Contact details

An `address` identifies contact information for a document or its nearest
`article` context; it is **not** a generic container for any street
address. Use a genuine support link or known contact method rather than an
invented email address. The example below uses the project's actual issue
tracker.

~~~html
<footer>
  <address>Questions about this guide?
    <a href="https://github.com/dporkka/syntyr-css/issues">
      Contact the Syntyr maintainers through Issues
    </a>.
  </address>
</footer>
~~~

## Native FAQ disclosure

Use a `details` element and its **first child** `summary` for
disclosures. Give related items the same `name` for a browser-native
single-open accordion. A single group member may start with `open`; browsers
close its peers when another member opens. This is an interaction, not a
tablist, so do not add `role="tab"` or extra JavaScript. Keep answers present
in the document for users and search engines. The optional stylesheet
distinguishes an opened panel with a soft border.

~~~html
<section aria-labelledby="faq-heading">
  <h2 id="faq-heading">FAQ</h2>
  <details name="syn-semantic-faq" open>
    <summary>Does this need JavaScript?</summary>
    <p>No. The browser handles open and closed state and keyboard use.</p>
  </details>
  <details name="syn-semantic-faq">
    <summary>Can I use it in a server-rendered app?</summary>
    <p>Yes. Keep the markup on the page and the group name unique.</p>
  </details>
</section>
~~~

For content that should be visible simultaneously, omit the shared `name`.
Do not hide legal, essential or time-critical information behind an unannounced
disclosure.

## Semantic issue search

Use `search` for the page's search landmark and a native GET form, with a
visible label and an actual endpoint. This example searches the public Syntyr
GitHub issue tracker; it works without client-side JavaScript, although
submitting navigates away to GitHub.

~~~html
<search>
  <form action="https://github.com/dporkka/syntyr-css/issues" method="get">
    <label for="issues-query">Search Syntyr issues</label>
    <input id="issues-query" type="search" name="q" required
           placeholder="Example: accessibility">
    <button type="submit">Find issues</button>
  </form>
</search>
~~~

The host application is responsible for providing a real backend for any
site-local search. Do not present a demo-only search box as functional.

## Grouped choice form

Use `fieldset` and `legend` for the shared form prompt, `label` for
control identification, and `optgroup` to group related `option`
elements. Native select popup appearance is browser-owned. Here the chosen
topic is sent as a GET query to the real public issue tracker.

~~~html
<form action="https://github.com/dporkka/syntyr-css/issues" method="get">
  <fieldset>
    <legend>Browse a topic</legend>
    <label for="issue-topic">Issue topic</label>
    <select name="q" id="issue-topic" required>
      <option value="">Choose a topic</option>
      <optgroup label="HTML">
        <option value="semantic">Semantic HTML</option>
        <option value="accessibility">Accessibility</option>
      </optgroup>
      <optgroup label="Styles">
        <option value="css">CSS</option>
        <option value="themes">Themes</option>
      </optgroup>
    </select>
    <button type="submit">View matching issues</button>
  </fieldset>
</form>
~~~

Do not replace `fieldset` with a visually similar generic container where
controls genuinely share a question.

## Progress and measurement

Use `progress[value][max]` for progress **toward completion**. Use
`meter[value][min][max]` for a bounded measurement such as utilization or a
rating. The `low`, `high` and `optimum` attributes describe value
quality, not completion progress. Include an actual `label` (or equivalent
accessible name) and visible readable value. `output` can display a
server-computed result; it does **not** recalculate automatically in response
to changing inputs without host logic.

~~~html
<section aria-labelledby="status-heading">
  <h2 id="status-heading">Illustrative status</h2>
  <label for="review-progress">Review progress: 7 of 10 complete</label>
  <progress id="review-progress" value="7" max="10">7 of 10</progress>
  <label for="capacity-meter">Sample capacity: 68%</label>
  <meter id="capacity-meter" value="68" min="0" max="100"
         low="30" high="85" optimum="70">68%</meter>
  <p>Calculated review total:
    <output name="review-total">7 completed reviews</output>
  </p>
</section>
~~~

All figures in this example are illustrative rather than live metrics.
For indeterminate progress, omit `value` and provide an accompanying
status message.

## Responsive captioned media

Use `picture` and `source[media][srcset]` for browser-driven responsive
art direction, `img` with meaningful alternative text and intrinsic
dimensions to prevent layout shifts, and `figure` with `figcaption` when a
caption belongs to the media. This example switches between two actual
Syntyr Studio screenshots at narrow widths. There is no carousel or script.

~~~html
<figure>
  <picture>
    <source media="(max-width: 600px)"
            srcset="../docs/previews/studio-settings.webp">
    <img src="../docs/previews/studio-editor.webp"
         width="1120" height="700" loading="lazy" decoding="async"
         alt="Syntyr Studio interface: settings on small screens and editor on larger screens">
  </picture>
  <figcaption>Two Syntyr Studio views, selected by viewport width.</figcaption>
</figure>
~~~

Supply valid paths relative to the **published page**, not the Markdown
document location. These paths assume the snippet runs in the examples
directory as in the live component gallery. If there is no meaningful
art-direction change, prefer a single responsive `img` instead.

## Native suggestions with datalist

Use `input[list]` with an associated `datalist` when you want to
**suggest** common text entries without restricting what the user can type.
Unlike `select`, it does not create an exhaustive set of choices. The
`input` still needs a visible `label`, a real `name` for submission, and
server-side validation. The browser owns how suggestions appear; do not try
to skin a datalist popup.

This working example submits a GET query to Syntyr's public issue tracker.

~~~html
<form action="https://github.com/dporkka/syntyr-css/issues" method="get">
  <label for="topic-suggest">Search issues (try a suggested topic)</label>
  <input id="topic-suggest" name="q" type="search"
         list="reference-topic-suggestions" required
         placeholder="Type a topic">
  <datalist id="reference-topic-suggestions">
    <option value="semantic"></option>
    <option value="accessibility"></option>
    <option value="themes"></option>
    <option value="typography"></option>
  </datalist>
  <button type="submit">Search issues on GitHub</button>
</form>
~~~

**No JavaScript is required** for suggestions. Use `select` instead when
the submitted value must come from a finite set.

## Glossary and abbreviations

Use a real definition list for a collection of terms and their definitions.
`dfn` identifies the term being defined, and `abbr[title]` expands an
abbreviation the first time it matters. Do not use `dfn` as a decorative
italic treatment or `dl` as an arbitrary two-column layout.

~~~html
<section aria-labelledby="glossary-heading">
  <h2 id="glossary-heading">Glossary</h2>
  <dl>
    <dt><dfn>Native semantics</dfn></dt>
    <dd>Meaning provided by HTML elements without custom roles.</dd>
    <dt><dfn>ARIA</dfn></dt>
    <dd><abbr title="Accessible Rich Internet Applications">ARIA</abbr>
        extends accessibility semantics only where native HTML is insufficient.</dd>
  </dl>
</section>
~~~

## Highlighted excerpts and quotations

`mark` indicates a relevant excerpt in its current context, such as a
search match, while `q` denotes an inline quotation. The `cite` element
names the cited **work**, rather than the author or a source URL. Do not
manually insert quote-mark characters around `q` when the browser already
provides them. Syntyr already styles `mark`, `q`, and `cite`; no extra
components or runtime are necessary.

~~~html
<article aria-labelledby="excerpt-heading">
  <h2 id="excerpt-heading">Highlighted documentation excerpt</h2>
  <p><mark>Native HTML</mark> allows browser-owned focus and semantics.</p>
  <p><q>Syntyr styles these elements without replacing browser semantics</q>
     — <cite><a href="../docs/semantic-components.html">
       Semantic HTML component recipes</a></cite>.</p>
</article>
~~~

The quoted line comes from this guide's introduction. For search results,
the server supplies the real match and safely escaped text; never inject
untrusted HTML into highlighted excerpts.

## Chronological ordered list

Use `ol` for genuinely ordered events and `time[datetime]` for dates
that machines can parse. `reversed` and `start` preserve native
numbering for newest-first sequences; they are not substitutes for sorting
the data server-side. This checklist is illustrative, **not** an actual
Syntyr release history.

~~~html
<section aria-labelledby="history-heading">
  <h2 id="history-heading">Illustrative release steps</h2>
  <ol reversed start="3">
    <li><time datetime="2026-11-16">16 November 2026</time>: Publish examples</li>
    <li><time datetime="2026-11-15">15 November 2026</time>: Validate HTML</li>
    <li><time datetime="2026-11-14">14 November 2026</time>: Draft content</li>
  </ol>
</section>
~~~

Use normal `ol` without `reversed` for a conventional chronological
timeline or instructions progressing from step one.

## Mathematical notation with MathML

Native **MathML** gives equations structural meaning: `math`, `mrow`,
`mi`, `mn`, `mo`, and `msup` identify the formula and its parts.
Include readable explanatory text in a `figcaption`; avoid images of
math without meaningful text alternatives. Annotation may preserve
source notation for compatible tools, but browsers own layout.

~~~html
<figure>
  <math display="block">
    <semantics>
      <mrow>
        <msup><mi>a</mi><mn>2</mn></msup>
        <mo>+</mo>
        <msup><mi>b</mi><mn>2</mn></msup>
        <mo>=</mo>
        <msup><mi>c</mi><mn>2</mn></msup>
      </mrow>
      <annotation encoding="application/x-tex">a^2 + b^2 = c^2</annotation>
    </semantics>
  </math>
  <figcaption>Example Pythagorean identity: a squared plus b squared equals c squared.</figcaption>
</figure>
~~~

MathML is browser-native, **not styled by the optional semantic sheet**.
Test presentation and accessibility with the actual browsers your users
need to support.

## Resource command list

A native `menu` is an unordered list of **commands/actions**, not an ARIA
application menu with arrow-key behavior. Use actual links for navigation
actions and `button` only when it performs an implemented action. Do not
add `role="menu"` unless you intend to implement its complete keyboard
interaction contract.

~~~html
<section aria-labelledby="resources-heading">
  <h2 id="resources-heading">Reference actions</h2>
  <menu>
    <li><a href="../docs/semantic-components.html">Read semantic recipes</a></li>
    <li><a href="native-elements.html">Browse native controls</a></li>
    <li><a href="https://github.com/dporkka/syntyr-css/issues">Report an issue</a></li>
  </menu>
</section>
~~~

All destinations are real links. Ordinary `ul` remains preferable for
a list of information rather than actions.

**Accessibility and maintenance:** Keep real heading order and link destinations,
avoid adding redundant ARIA roles to native elements, test browser reflow and
right-to-left content, and do not add JavaScript just to imitate HTML controls.
`ruby`, `bdi`, `bdo`, `rp` and table navigation are browser-owned behavior.
