// Framework-free Custom Elements demonstration, never bundled with Syntyr CSS.
export class DemoNativeStatus extends HTMLElement {
  static observedAttributes = ["service", "online", "busy"];

  constructor() {
    super();
    this._listeners = null;
    this._toggle = () => {
      if (this.busy) return;
      this.online = !this.online;
      this.dispatchEvent(new CustomEvent("syn-demo-native-status-change", {
        detail: { service: this.service, online: this.online },
        bubbles: true,
        composed: true,
      }));
    };
  }
  get service() { return this.getAttribute("service") ?? "Service"; }
  set service(value) { this.setAttribute("service", String(value)); }
  get online() { return this.hasAttribute("online"); }
  set online(value) { this.toggleAttribute("online", Boolean(value)); }
  get busy() { return this.hasAttribute("busy"); }
  set busy(value) { this.toggleAttribute("busy", Boolean(value)); }

  connectedCallback() {
    // Preserve existing Declarative Shadow DOM markup during upgrade.
    if (!this.shadowRoot) {
      const root = this.attachShadow({ mode: "open" });
      const stylesheet = document.createElement("link");
      stylesheet.rel = "stylesheet";
      stylesheet.href = new URL("./status-toggle.css", import.meta.url).href;
      const panel = document.createElement("section");
      panel.setAttribute("part", "panel");
      // Fixed structural markup only; dynamic values are assigned with textContent.
      panel.innerHTML = `<div data-busy-region>
          <h3 part="title"></h3>
          <button part="toggle" type="button"></button>
        </div>
        <p part="status" role="status"></p>`;
      root.append(stylesheet, panel);
    }
    this._listeners?.abort();
    this._listeners = new AbortController();
    this.shadowRoot.querySelector('[part="toggle"]')?.addEventListener(
      "click", this._toggle, { signal: this._listeners.signal });
    this._render();
  }

  disconnectedCallback() {
    this._listeners?.abort();
    this._listeners = null;
  }

  attributeChangedCallback() {
    if (this.isConnected) this._render();
  }

  _render() {
    const panel = this.shadowRoot?.querySelector('[part="panel"]');
    const title = panel?.querySelector('[part="title"]');
    const status = panel?.querySelector('[part="status"]');
    const button = panel?.querySelector('[part="toggle"]');
    const busyRegion = panel?.querySelector("[data-busy-region]");
    if (!title || !status || !button || !busyRegion) return;
    if (title.textContent !== this.service) title.textContent = this.service;
    busyRegion.setAttribute("aria-busy", String(this.busy));
    // Avoid re-announcing an unchanged live region when unrelated attributes change.
    const nextStatus = this.busy ? "Updating status…" : this.online ? "Online" : "Offline";
    if (status.textContent !== nextStatus) status.textContent = nextStatus;
    // The SSR button starts disabled and becomes interactive only after upgrade.
    button.disabled = this.busy;
    // Changing action text makes this a normal button, not an aria-pressed toggle.
    const nextAction = this.busy ? "Updating…" : this.online ? "Mark offline" : "Mark online";
    if (button.textContent !== nextAction) button.textContent = nextAction;
  }
}

// Repeated imports (e.g. different bundler URLs) must not define the same tag twice.
if (!customElements.get("syn-demo-native-status")) {
  customElements.define("syn-demo-native-status", DemoNativeStatus);
}
