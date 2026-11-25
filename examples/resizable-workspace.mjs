/* Optional copy-owned enhancement for a single workspace. No Syntyr CSS runtime. */
for (const workspace of document.querySelectorAll("[data-syn-resizable]")) {
  const panes = workspace.querySelector(".syn-resizable-workspace__panes");
  const separator = workspace.querySelector(".syn-resizable-workspace__separator");
  if (!panes || !separator) continue;
  const minimum = Number(separator.getAttribute("aria-valuemin"));
  const maximum = Number(separator.getAttribute("aria-valuemax"));
  let percentage = Number(separator.getAttribute("aria-valuenow"));
  let pointer = null;
  let grabOffset = 0;

  function update(value) {
    if (!Number.isFinite(value)) return;
    percentage = Math.min(maximum, Math.max(minimum, Math.round(value)));
    panes.style.setProperty("--syn-workspace-leading", percentage + "%");
    separator.setAttribute("aria-valuenow", String(percentage));
    separator.setAttribute("aria-valuetext", "Inventory pane " + percentage + " percent");
  }
  function fromPointer(clientX) {
    const rect = panes.getBoundingClientRect();
    if (rect.width <= 0) return;
    const direction = getComputedStyle(panes).direction;
    // The grab offset measures from the separator edge adjacent to the
    // leading pane, so pressing its centre never moves the split.
    const leadingPixels = direction === "rtl"
      ? rect.right - clientX - grabOffset
      : clientX - rect.left - grabOffset;
    update(leadingPixels / rect.width * 100);
  }

  separator.hidden = false;
  separator.tabIndex = 0;
  workspace.setAttribute("data-syn-interactive", "");
  update(percentage);

  separator.addEventListener("pointerdown", event => {
    if (pointer !== null || event.button !== 0) return;
    // Only moves resize the panel; a stationary pointerdown is a no-op.
    const handle = separator.getBoundingClientRect();
    const direction = getComputedStyle(panes).direction;
    grabOffset = direction === "rtl"
      ? handle.right - event.clientX
      : event.clientX - handle.left;
    pointer = event.pointerId;
    separator.setPointerCapture(pointer);
    event.preventDefault();
  });
  separator.addEventListener("pointermove", event => {
    if (pointer === event.pointerId) fromPointer(event.clientX);
  });
  function finish(event) {
    if (pointer !== event.pointerId) return;
    pointer = null;
    if (separator.hasPointerCapture(event.pointerId)) {
      separator.releasePointerCapture(event.pointerId);
    }
  }
  separator.addEventListener("pointerup", finish);
  separator.addEventListener("pointercancel", finish);
  separator.addEventListener("lostpointercapture", event => {
    if (event.pointerId === pointer) pointer = null;
  });

  separator.addEventListener("keydown", event => {
    const direction = getComputedStyle(panes).direction;
    const step = event.shiftKey ? 10 : 2;
    let next;
    if (event.key === "ArrowRight") next = percentage + (direction === "rtl" ? -step : step);
    else if (event.key === "ArrowLeft") next = percentage + (direction === "rtl" ? step : -step);
    else if (event.key === "Home") next = minimum;
    else if (event.key === "End") next = maximum;
    else return;
    event.preventDefault();
    update(next);
  });
}
