// Optional application-owned demonstration, not part of Syntyr CSS.
// Enhances two genuine native inputs rather than replacing them.
class DemoAssetRange extends HTMLElement {
  static formAssociated = true;
  static observedAttributes = ["name", "required"];

  constructor() {
    super();
    this._internals = this.attachInternals();
    this._listeners = null;
    this._disabledByForm = false;
    this._min = null;
    this._max = null;
    this._restore = null;
  }

  get form() { return this._internals.form; }
  get validity() { return this._internals.validity; }
  get validationMessage() { return this._internals.validationMessage; }
  get willValidate() { return this._internals.willValidate; }
  checkValidity() { return this._internals.checkValidity(); }
  reportValidity() { return this._internals.reportValidity(); }

  connectedCallback() {
    this._min = this.querySelector("[data-asset-min]");
    this._max = this.querySelector("[data-asset-max]");
    if (!this._min || !this._max) return;

    // When JS is disabled, these names stay on the native inputs. In the
    // enhanced case, ElementInternals becomes the sole submitter of the pair.
    this._min.removeAttribute("name");
    this._max.removeAttribute("name");
    this._listeners?.abort();
    this._listeners = new AbortController();
    for (const input of [this._min, this._max]) {
      input.addEventListener("input", () => this._sync(), {
        signal: this._listeners.signal,
      });
      input.addEventListener("change", () => this._sync(), {
        signal: this._listeners.signal,
      });
    }
    if (this._restore !== null) {
      this._applyRestoredState(this._restore);
      this._restore = null;
    }
    this._syncDisabled();
    this._sync();
    this.setAttribute("data-enhanced", "");
  }

  disconnectedCallback() {
    this._listeners?.abort();
    this._listeners = null;
  }

  attributeChangedCallback() {
    if (this.isConnected && this._min && this._max) this._sync();
  }

  formDisabledCallback(disabled) {
    // Do not reflect disabled onto the host: a disabled ancestor fieldset
    // must be able to re-enable the control.
    this._disabledByForm = disabled;
    this._syncDisabled();
  }

  formResetCallback() {
    if (!this._min || !this._max) return;
    this._min.value = this._min.defaultValue;
    this._max.value = this._max.defaultValue;
    this._sync();
  }

  formStateRestoreCallback(state) {
    if (typeof state !== "string") return;
    if (!this._min || !this._max) {
      this._restore = state;
      return;
    }
    this._applyRestoredState(state);
    this._sync();
  }

  _applyRestoredState(state) {
    let parts;
    try { parts = JSON.parse(state); } catch { return; }
    if (!Array.isArray(parts) || parts.length !== 2 ||
        !parts.every(value => typeof value === "string")) return;
    this._min.value = parts[0];
    this._max.value = parts[1];
  }

  _syncDisabled() {
    if (!this._min || !this._max) return;
    this._min.disabled = this._disabledByForm;
    this._max.disabled = this._disabledByForm;
  }

  _sync() {
    if (!this._min || !this._max) return;
    // Native fallback is required when JS is absent; the upgraded inputs
    // follow the host attribute when applications change it dynamically.
    this._min.required = this.hasAttribute("required");
    this._max.required = this.hasAttribute("required");
    const lower = this._min.value;
    const upper = this._max.value;
    const name = this.getAttribute("name");
    if (name) {
      const data = new FormData();
      data.append(`${name}_min`, lower);
      data.append(`${name}_max`, upper);
      this._internals.setFormValue(data, JSON.stringify([lower, upper]));
    } else {
      this._internals.setFormValue(null);
    }

    let message = "";
    if (this.hasAttribute("required") && (!lower || !upper)) {
      message = "Enter a minimum and maximum asset count.";
      this._internals.setValidity({ valueMissing: true }, message,
        !lower ? this._min : this._max);
    } else if (lower !== "" && upper !== "" &&
               this._min.validity.valid && this._max.validity.valid &&
               Number(lower) > Number(upper)) {
      message = "Minimum assets cannot exceed maximum assets.";
      this._internals.setValidity({ customError: true }, message, this._max);
    } else {
      this._internals.setValidity({});
    }
    this.toggleAttribute("data-range-invalid", Boolean(message));
    const error = this.querySelector("[data-asset-error]");
    if (error) error.textContent = message;
  }
}

// Feature detection preserves native controls on older browsers:
if ("attachInternals" in HTMLElement.prototype &&
    typeof ElementInternals !== "undefined" &&
    "setFormValue" in ElementInternals.prototype) {
  customElements.define("syn-demo-asset-range", DemoAssetRange);
}
