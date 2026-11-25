# Native business workflows

This source-candidate recipe extends Syntyr's optional `syntyr.recipes.css` with
file-upload presentation, an action footer, and nested resource navigation.
It composes the existing `.syn-detail-layout` and `.syn-error-summary`;
there is no separate master-detail runtime, file-drop library, or custom treeview.
See the [script-free example](../examples/native-workflows.html).

## Use plain HTML

Load the version-matched `syntyr.core.css` and `syntyr.recipes.css`.
Place the classes inside `.syn-root`, with an explicit theme when desired.
The styles are opt-in and no JavaScript is required to expand folders, pick
files, jump to records, or associate submit buttons with the form.

### Uploads and explicit submit intents

```html
<form id="resource-editor" action="/resources/42" method="post"
      enctype="multipart/form-data">
  <!-- Application supplies an actual CSRF token for this request. -->
  <label for="files">Attachments</label>
  <div class="syn-upload-field">
    <input class="syn-input" id="files" type="file" name="attachments"
           accept="image/png,image/jpeg,application/pdf" multiple
           aria-describedby="files-help">
    <p id="files-help">Choose images or PDF documents.</p>
  </div>
</form>
<footer class="syn-form-actions">
  <div class="syn-form-actions__buttons">
    <button class="syn-button" form="resource-editor" type="submit"
            name="intent" value="save">Save</button>
    <button class="syn-button syn-button--primary"
            form="resource-editor" type="submit"
            name="intent" value="save-close">Save and close</button>
  </div>
</footer>
```

The HTML `form` attribute associates buttons outside the `form` element
with that form. Only the clicked submit button's `intent` value is sent,
so the server can choose the correct action. A third-party HTMX or React
runtime is not necessary for native submission; use one only for application
behaviors that require it. Do not use `method="dialog"` for a save action.

The **server** must enforce authenticated object-level authorization, CSRF
protection, request size limits, file size limits, MIME/content verification,
extension and malware policies, safe storage, and error recovery. The
`accept` attribute is merely picker guidance, **not** validation. Preserve
selected intent on failed validation, and return accessible error messages.
For any mutation that changes records, enforce authorization regardless of
which submitter was used. Existing attachments are application data, not
newly selected files.

The public example disables both POST buttons because it has no endpoint.
A real application may enable them only when its endpoint exists and handles
both intents correctly. The browser owns the file chooser. Drag-and-drop can
be added in an application but cannot replace the keyboard-operable file input.

### Resource disclosure navigation and master-detail links

```html
<div class="syn-detail-layout">
  <aside class="syn-detail-aside">
    <nav aria-label="Resources">
      <ul>
        <li><details class="syn-details" open><summary>North</summary>
          <ul><li><a href="#record-42">Resource 42</a></li></ul>
        </details></li>
      </ul>
    </nav>
  </aside>
  <section class="syn-detail-main" aria-label="Record details">
    <article id="record-42" tabindex="-1">
      <h2>Resource 42</h2>
    </article>
  </section>
</div>
```

Use genuine nested `ul`, `details`, and `summary`, with ordinary links.
This is **disclosure navigation**, not an ARIA treeview; do not add
`role="tree"` or `role="treeitem"` without implementing the full keyboard
model. Each anchor must target a real element or working server route.
For server-rendered selection, render the selected record and use
`aria-current="page"` on its corresponding link only.

At narrow widths, the existing detail shell wraps the sidebar above
the inspector. File-picker padding and attachment-list indentation are bounded
by viewport width to avoid horizontal overflow with enlarged browser text. RTL relies on logical padding and borders; focus outlines
and forced-colors borders remain visible. Verify keyboard navigation,
200% and 400% zoom, and focus after postback using a real browser.
If asynchronous updates are introduced, the host application owns focus,
history, announcements and saved-state feedback.

### Avoid duplicate components

- Reuse `.syn-error-summary` for failed server responses, and link the
  summary to invalid fields.
- Reuse `.syn-detail-layout`, `.syn-detail-main` and `.syn-detail-aside`
  rather than inventing a new split-view primitive.
- Reuse native file controls and core `.syn-input` styling; Syntyr does
  not implement upload progress, storage, directory traversal or drag/drop.
