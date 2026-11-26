// Syntyr form customizer: portable native-HTML model. No DOM or runtime dependencies.
export const FORM_SCHEMA = "syntyr.form.v1";
export const FIELD_TYPES = Object.freeze([
  "text", "email", "tel", "url", "number", "date",
  "textarea", "select", "radio", "checkbox", "file"
]);
export const FORM_THEMES = Object.freeze([
  "studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"
]);
export const FORM_TEMPLATES = Object.freeze(["contact", "feedback", "newsletter", "blank"]);

const DEFAULTS = {
  text: ["Text field", "text_field"],
  email: ["Email address", "email"],
  tel: ["Phone number", "phone"],
  url: ["Website", "website"],
  number: ["Quantity", "quantity"],
  date: ["Date", "date"],
  textarea: ["Message", "message"],
  select: ["Select an option", "selection"],
  radio: ["Choose one", "choice"],
  checkbox: ["I agree", "agreement"],
  file: ["Attachment", "attachment"]
};
const RESERVED = new Set(["__proto__", "constructor", "prototype"]);

function field(id, type, name, label, required = false, extras = {}) {
  return { id, type, name, label, required, placeholder: "",
    help: "", options: [], ...extras };
}

export function createForm(template = "contact") {
  if (!FORM_TEMPLATES.includes(template)) throw new Error("Unknown form template");
  const form = {
    schema: FORM_SCHEMA, title: "Contact us",
    description: "Tell us how we can help.",
    action: "/contact", method: "post", theme: "studio",
    submitLabel: "Send message", fields: [
      field("name", "text", "full_name", "Full name", true, { placeholder: "Your name" }),
      field("email", "email", "email", "Email address", true, { placeholder: "you@example.com" }),
      field("message", "textarea", "message", "Message", true)
    ]
  };
  if (template === "newsletter") return {
    ...form, title: "Subscribe to updates", description: "Get occasional product updates.",
    action: "/subscribe", submitLabel: "Subscribe",
    fields: [field("email", "email", "email", "Email address", true, { placeholder: "you@example.com" })]
  };
  if (template === "feedback") return {
    ...form, title: "Share feedback", description: "Help us improve.",
    action: "/feedback", submitLabel: "Send feedback",
    fields: [
      field("rating", "select", "rating", "How was your experience?", true,
        { options: ["Excellent", "Good", "Fair", "Poor"] }),
      field("feedback", "textarea", "feedback", "Your feedback", true),
      field("reply", "checkbox", "allow_reply", "You may contact me about this feedback")
    ]
  };
  if (template === "blank") return {
    ...form, title: "New form", description: "",
    action: "/submit", submitLabel: "Submit", fields: []
  };
  return form;
}

const textValue = (value, name, limit = 180, allowBlank = true) => {
  if (typeof value !== "string" || value.length > limit || (!allowBlank && !value.trim())) {
    throw new Error(name + " must be a nonempty string of at most " + limit + " characters");
  }
  return value.trim();
};
const escapeHtml = value => String(value).replace(/&/g, "&amp;")
  .replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
const attr = (name, value) => value ? " " + name + '="' + escapeHtml(value) + '"' : "";
const requiredAttr = value => value ? " required" : "";

function validAction(action) {
  // Keep relative same-origin routes, HTTPS, and explicitly local HTTP development.
  // Reject browser-normalized whitespace/backslashes and credentials in destinations.
  const invalid = () => { throw new Error("Form action must be a relative path, an HTTPS URL, or a loopback HTTP development URL"); };
  if (/[<>"'\s\\\x00-\x1f\x7f]/.test(action)) invalid();
  if (/^(?:\/(?!\/)|\.\/|\.\.\/)[^\s]*$/.test(action)) return action;
  if (!/^https?:\/\/[^/?#]+(?:[/?#].*)?$/i.test(action)) invalid();
  let url;
  try { url = new URL(action); } catch { invalid(); }
  if (url.username || url.password) invalid();
  if (url.protocol !== "https:" &&
      !(url.protocol === "http:" && /^http:\/\/(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]+)?(?:[/?#]|$)/i.test(action))) invalid();
  return action;
}

export function validateForm(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("Form must be an object");
  }
  if (input.schema !== FORM_SCHEMA) throw new Error("Unsupported form schema");
  const title = textValue(input.title, "Title", 160, false);
  const description = textValue(input.description, "Description", 500);
  const action = validAction(textValue(input.action, "Action", 500, false));
  const method = input.method;
  if (!["get", "post"].includes(method)) throw new Error("Method must be GET or POST");
  if (!FORM_THEMES.includes(input.theme)) throw new Error("Unknown theme");
  const submitLabel = textValue(input.submitLabel, "Submit label", 100, false);
  if (!Array.isArray(input.fields) || input.fields.length > 50) {
    throw new Error("Too many fields (maximum 50)");
  }
  const ids = new Set();
  const names = new Set();
  const fields = input.fields.map((item, index) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new Error("Field " + (index + 1) + " must be an object");
    }
    if (!FIELD_TYPES.includes(item.type)) throw new Error("Unknown field type");
    const id = textValue(item.id, "Field id", 64, false);
    if (!/^[a-z][a-z0-9_-]*$/i.test(id) || ids.has(id)) {
      throw new Error("Invalid or duplicate field id");
    }
    ids.add(id);
    const name = textValue(item.name, "Field name", 64, false);
    if (!/^[a-z][a-z0-9_-]*$/i.test(name) || RESERVED.has(name) || names.has(name)) {
      throw new Error("Invalid or duplicate field name");
    }
    names.add(name);
    const label = textValue(item.label, "Field label", 160, false);
    const placeholder = textValue(item.placeholder ?? "", "Placeholder", 160);
    const help = textValue(item.help ?? "", "Help text", 300);
    if (item.required != null && typeof item.required !== "boolean") {
      throw new Error("Required must be a boolean");
    }
    if (item.options != null && !Array.isArray(item.options)) {
      throw new Error("Options must be a list of strings");
    }
    let options = [];
    if (item.type === "select" || item.type === "radio") {
      options = (item.options ?? []).map((option) => textValue(option, "Option", 120, false));
      if (options.length < 2 || options.length > 20 || new Set(options).size !== options.length) {
        throw new Error("Select and radio fields need 2–20 distinct options");
      }
    }
    return { id, type: item.type, name, label, required: item.required === true,
      placeholder, help, options };
  });
  if (method === "get" && fields.some(item => item.type === "file")) {
    throw new Error("File fields require POST");
  }
  return { schema: FORM_SCHEMA, title, description, action, method,
    theme: input.theme, submitLabel, fields };
}

export function addField(input, type) {
  if (!FIELD_TYPES.includes(type)) throw new Error("Unknown field type");
  const form = validateForm(input);
  if (form.fields.length === 50) throw new Error("Too many fields");
  const [label, baseName] = DEFAULTS[type];
  let count = 1;
  while (form.fields.some(item => item.id === "field-" + count)) count++;
  let name = baseName;
  let suffix = 2;
  while (form.fields.some(item => item.name === name)) name = baseName + "_" + suffix++;
  const added = field("field-" + count, type, name, label, false,
    (type === "select" || type === "radio") ? { options: ["Option 1", "Option 2"] } : {});
  // A GET form cannot contain file inputs; make the transport correct automatically.
  return { ...form, method: type === "file" ? "post" : form.method,
    fields: [...form.fields, added] };
}

export function moveField(input, fromIndex, toIndex) {
  const form = validateForm(input);
  if (!Number.isInteger(fromIndex) || !Number.isInteger(toIndex) ||
      fromIndex < 0 || toIndex < 0 || fromIndex >= form.fields.length ||
      toIndex >= form.fields.length) throw new Error("Field index out of range");
  const fields = form.fields.slice();
  fields.splice(toIndex, 0, fields.splice(fromIndex, 1)[0]);
  return { ...form, fields };
}

// Scope IDs to the form instance, including across separately opened editors.
const formNamespaces = new WeakMap();

function namespaceFor(input) {
  if (!formNamespaces.has(input)) {
    const bytes = globalThis.crypto.getRandomValues(new Uint8Array(12));
    formNamespaces.set(input, Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join(""));
  }
  return formNamespaces.get(input);
}

function renderField(item, namespace) {
  const id = "syn-field-" + namespace + "-" + item.id;
  const helpId = "syn-help-" + namespace + "-" + item.id;
  const help = item.help
    ? '<p class="syn-help" id="' + helpId + '">' + escapeHtml(item.help) + "</p>"
    : "";
  const describedBy = item.help ? ' aria-describedby="' + helpId + '"' : "";
  const fieldStart = '<div class="syn-field">';
  const fieldEnd = "</div>";
  const label = '<label class="syn-label" for="' + id + '">' +
    escapeHtml(item.label) + "</label>";
  const shared = ' id="' + id + '" name="' + escapeHtml(item.name) + '"' +
    describedBy + requiredAttr(item.required);
  if (item.type === "checkbox") {
    return fieldStart + '<label class="syn-check" for="' + id + '">' +
      '<input class="syn-input" type="checkbox"' + shared + ' value="yes"> ' +
      '<span>' + escapeHtml(item.label) + "</span></label>" + help + fieldEnd;
  }
  if (item.type === "select") {
    return fieldStart + label + '<select class="syn-select"' + shared + ">" +
      '<option value="">Choose an option</option>' +
      item.options.map(option => '<option value="' + escapeHtml(option) + '">' +
        escapeHtml(option) + "</option>").join("") + "</select>" + help + fieldEnd;
  }
  if (item.type === "radio") {
    return '<fieldset class="syn-fieldset"><legend>' + escapeHtml(item.label) +
      "</legend>" + item.options.map((option, index) =>
        '<label class="syn-check"><input class="syn-input" type="radio" name="' +
        escapeHtml(item.name) + '" value="' + escapeHtml(option) + '"' +
        (item.required && index === 0 ? " required" : "") +
        describedBy + '> <span>' + escapeHtml(option) + "</span></label>"
      ).join("") + help + "</fieldset>";
  }
  if (item.type === "textarea") {
    return fieldStart + label + '<textarea class="syn-textarea" rows="4"' +
      shared + attr("placeholder", item.placeholder) + "></textarea>" + help + fieldEnd;
  }
  return fieldStart + label + '<input class="syn-input" type="' + item.type + '"' +
    shared + attr("placeholder", item.placeholder) + ">" + help + fieldEnd;
}

export function renderForm(input) {
  const form = validateForm(input);
  return renderValidatedForm(form, namespaceFor(input));
}

function renderValidatedForm(form, namespace) {
  const multipart = form.fields.some(item => item.type === "file")
    ? ' enctype="multipart/form-data"' : "";
  const description = form.description
    ? '<p class="syn-muted">' + escapeHtml(form.description) + "</p>" : "";
  return '<section class="syn-root" data-syn-theme="' + form.theme + '">' +
    '<form class="syn-form" action="' + escapeHtml(form.action) +
    '" method="' + form.method + '"' + multipart + '>' +
    '<h2 class="syn-heading">' + escapeHtml(form.title) + "</h2>" +
    description + form.fields.map(item => renderField(item, namespace)).join("\n") +
    '<button class="syn-button syn-button--primary" type="submit">' +
    escapeHtml(form.submitLabel) + "</button></form></section>";
}

export function exportStandalone(input) {
  const form = validateForm(input);
  return '<!doctype html>\n<html lang="en">\n<head>\n' +
    '  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n' +
    "  <title>" + escapeHtml(form.title) + "</title>\n" +
    '  <link rel="stylesheet" href="syntyr.core.css">\n</head>\n' +
    '<body class="syn-root syn-page" data-syn-theme="' + form.theme + '">\n' +
    '  <main class="syn-shell">\n' + renderValidatedForm(form, namespaceFor(input)) +
    "\n  </main>\n</body>\n</html>\n";
}
