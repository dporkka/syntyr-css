/* Copy-owned, optional command navigation adapter; not shipped in core CSS.
   Uses a native modal dialog and ordinary anchors, not an ARIA combobox. */
const normalized = (value) => value.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();

/** All query words must occur in the destination's visible label or keywords. */
export function matchCommand(labelAndKeywords, query) {
  const haystack = normalized(labelAndKeywords);
  return normalized(query).trim().split(/\s+/u).every((part) => haystack.includes(part));
}

if (typeof document !== "undefined") {
  const dialog = document.querySelector("[data-command-dialog]");
  const trigger = document.querySelector("[data-command-open]");
  const input = dialog?.querySelector("[data-command-query]");
  const status = dialog?.querySelector("[data-command-status]");
  const empty = dialog?.querySelector("[data-command-empty]");
  const close = dialog?.querySelector("[data-command-close]");
  const links = Array.from(dialog?.querySelectorAll("[data-command-item]") || []);

  if (dialog instanceof HTMLDialogElement && trigger && input && status && empty && close) {
    let previousFocus = null;

    function updateResults() {
      let count = 0;
      for (const link of links) {
        const item = link.closest("li");
        const matching = matchCommand(
          `${link.textContent} ${link.dataset.commandKeywords || ""}`, input.value,
        );
        if (item) item.hidden = !matching;
        if (matching) count += 1;
      }
      empty.hidden = count !== 0;
      status.textContent = `${count} ${count === 1 ? "destination" : "destinations"}`;
    }

    function openMenu() {
      if (dialog.open) return;
      previousFocus = document.activeElement;
      input.value = "";
      updateResults();
      dialog.showModal();
      input.focus();
    }

    // Do not apply an author-level display rule until enhancement is ready.
    // Otherwise .syn-button can override the user-agent [hidden] styling.
    trigger.classList.add("syn-button", "syn-button--primary");
    trigger.hidden = false;
    trigger.addEventListener("click", openMenu);
    close.addEventListener("click", () => dialog.close());
    input.addEventListener("input", updateResults);
    // Some browsers consume Escape to clear type=search before canceling dialog.
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !event.isComposing) {
        event.preventDefault();
        event.stopPropagation();
        dialog.close();
      }
    });
    dialog.addEventListener("close", () => {
      if (previousFocus?.isConnected && typeof previousFocus.focus === "function") {
        previousFocus.focus();
      }
      previousFocus = null;
    });
    document.addEventListener("keydown", (event) => {
      if (event.isComposing || event.repeat || event.altKey || event.shiftKey ||
          !(event.metaKey || event.ctrlKey) || event.key.toLowerCase() !== "k") return;
      event.preventDefault();
      if (dialog.open) dialog.close();
      else openMenu();
    });
    for (const link of links) link.addEventListener("click", () => dialog.close());
  }
}
