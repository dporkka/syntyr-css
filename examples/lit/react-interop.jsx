import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./status-panel.js";

// React 19 owns the application state; Lit owns the custom element internals.
function LitInReact() {
  const [result, setResult] = useState("Waiting for a native custom event");
  function handleStatus(event) {
    setResult(`${event.detail.service}: ${event.detail.online ? "online" : "offline"} (React 19 handler)`);
  }

  return (
    <section className="syn-panel">
      <h2 className="syn-heading">React 19 custom element</h2>
      <syn-demo-status-panel
        service="React customer hub"
        online
        onsyn-demo-status-change={handleStatus}
      />
      <p id="react-event-output" role="status" aria-live="polite">{result}</p>
    </section>
  );
}

createRoot(document.getElementById("react-root")).render(<LitInReact />);
