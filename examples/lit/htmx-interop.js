// The application owns both optional frameworks; Syntyr ships neither.
import "./status-panel.js";
import "htmx.org";

document.addEventListener("syn-demo-status-change", (event) => {
  const output = document.querySelector("#htmx-event-output");
  if (output) {
    output.textContent = `${event.detail.service}: ${event.detail.online ? "online" : "offline"} (after HTMX swap)`;
  }
});
