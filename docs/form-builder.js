import {
  FIELD_TYPES, createForm, addField, moveField,
  renderForm, exportStandalone, validateForm
} from "./form-builder-model.mjs";

const $ = id => document.getElementById(id);
let currentForm = createForm("contact");

const settings = {
  "form-theme": "theme",
  "form-title": "title",
  "form-description": "description",
  "form-action": "action",
  "form-method": "method",
  "form-submit-label": "submitLabel"
};
const typeLabels = {
  text: "Text", email: "Email", tel: "Phone", url: "URL",
  number: "Number", date: "Date", textarea: "Long text",
  select: "Select", radio: "Radio group", checkbox: "Checkbox", file: "File upload"
};

function setStatus(message, isError = false) {
  $("form-status").textContent = message;
  $("form-status").dataset.error = isError ? "true" : "false";
}

function updateOutput() {
  try {
    validateForm(currentForm);
    const markup = renderForm(currentForm);
    $("form-code").value = markup;
    $("form-preview").srcdoc =
      '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width, initial-scale=1">' +
      '<link rel="stylesheet" href="../dist/syntyr.core.css">' +
      '<style>body{margin:0;padding:1.25rem} .syn-root{max-width:58rem;margin:auto}</style>' +
      '</head><body class="syn-root syn-page" data-syn-theme="' +
      currentForm.theme + '">' + markup + '</body></html>';
    $("form-copy").disabled = false;
    $("form-download").disabled = false;
    setStatus("Valid HTML ready. Connect the action to your own submission handler before publishing.");
  } catch (error) {
    $("form-code").value = "";
    $("form-copy").disabled = true;
    $("form-download").disabled = true;
    $("form-preview").srcdoc =
      '<!doctype html><html lang="en"><body><p>Correct the configuration to preview this form.</p></body></html>';
    setStatus(error.message, true);
  }
}

function inputLabel(text, control) {
  const label = document.createElement("label");
  label.className = "syn-label";
  const title = document.createElement("span");
  title.textContent = text;
  label.append(title, control);
  return label;
}

function makeTextField(item, key, title, { wide = false, multiline = false } = {}) {
  const control = document.createElement(multiline ? "textarea" : "input");
  control.className = multiline ? "syn-textarea" : "syn-input";
  if (!multiline) control.type = "text";
  if (multiline) control.rows = 3;
  if (!multiline) control.maxLength = { name: 64, label: 160, placeholder: 160, help: 300 }[key] || 160;
  control.value = item[key] || "";
  control.addEventListener("input", () => {
    item[key] = control.value;
    updateOutput();
  });
  const wrapper = inputLabel(title, control);
  if (wide) wrapper.classList.add("form-builder-wide");
  return wrapper;
}

function makeTypeField(item) {
  const select = document.createElement("select");
  select.className = "syn-select";
  for (const type of FIELD_TYPES) {
    const option = new Option(typeLabels[type], type);
    select.add(option);
  }
  select.value = item.type;
  select.addEventListener("change", () => {
    item.type = select.value;
    if (item.type === "select" || item.type === "radio") {
      if (!item.options || item.options.length < 2) item.options = ["Option 1", "Option 2"];
    }
    if (item.type === "file") {
      currentForm.method = "post";
      $("form-method").value = "post";
    }
    drawFields();
    updateOutput();
  });
  return inputLabel("INPUT TYPE", select);
}

function makeRequiredField(item) {
  const label = document.createElement("label");
  label.className = "syn-check";
  const checkbox = document.createElement("input");
  checkbox.className = "syn-input";
  checkbox.type = "checkbox";
  checkbox.checked = Boolean(item.required);
  checkbox.addEventListener("change", () => {
    item.required = checkbox.checked;
    updateOutput();
  });
  const text = document.createElement("span");
  text.textContent = "Required field";
  label.append(checkbox, text);
  return label;
}

function drawFields() {
  const list = $("form-field-list");
  list.replaceChildren();
  currentForm.fields.forEach((item, index) => {
    const card = document.createElement("li");
    card.className = "form-builder-field";
    const heading = document.createElement("div");
    heading.className = "form-builder-field-title";
    const title = document.createElement("h3");
    title.textContent = (index + 1) + ". " + item.label;
    const actions = document.createElement("div");
    actions.className = "form-builder-field-actions";
    for (const [text, hint, offset] of [
      ["↑", "Move field up", -1], ["↓", "Move field down", 1]
    ]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "syn-button";
      button.textContent = text;
      button.title = hint;
      button.setAttribute("aria-label", hint + ": " + item.label);
      button.disabled = index + offset < 0 || index + offset >= currentForm.fields.length;
      button.addEventListener("click", () => {
        try {
          currentForm = moveField(currentForm, index, index + offset);
          drawFields();
          updateOutput();
        } catch (error) { setStatus(error.message, true); }
      });
      actions.append(button);
    }
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "syn-button";
    remove.textContent = "REMOVE";
    remove.setAttribute("aria-label", "Remove field: " + item.label);
    remove.addEventListener("click", () => {
      currentForm.fields.splice(index, 1);
      drawFields();
      updateOutput();
    });
    actions.append(remove);
    heading.append(title, actions);

    const controls = document.createElement("div");
    controls.className = "form-builder-field-controls";
    controls.append(makeTypeField(item));
    controls.append(makeTextField(item, "name", "SUBMISSION NAME"));
    controls.append(makeTextField(item, "label", "VISIBLE LABEL", { wide: true }));
    if (item.type !== "checkbox" && item.type !== "radio" && item.type !== "file") {
      controls.append(makeTextField(item, "placeholder", "PLACEHOLDER", { wide: true }));
    }
    controls.append(makeTextField(item, "help", "HELP TEXT", { wide: true }));
    if (item.type === "select" || item.type === "radio") {
      const textarea = document.createElement("textarea");
      textarea.className = "syn-textarea";
      textarea.rows = 4;
      textarea.value = (item.options || []).join("\n");
      textarea.setAttribute("aria-description", "One option on each line, at least two distinct options");
      textarea.addEventListener("input", () => {
        item.options = textarea.value.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
        updateOutput();
      });
      controls.append(inputLabel("OPTIONS (ONE PER LINE)", textarea));
      controls.lastElementChild.classList.add("form-builder-wide");
    }
    controls.append(makeRequiredField(item));
    card.append(heading, controls);
    list.append(card);
  });
  if (!currentForm.fields.length) {
    const empty = document.createElement("li");
    empty.className = "syn-caption";
    empty.textContent = "No fields yet. Choose a field type and select Add field.";
    list.append(empty);
  }
}

function syncSettings() {
  for (const [id, property] of Object.entries(settings)) {
    $(id).value = currentForm[property];
  }
}

function resetToTemplate(template) {
  currentForm = createForm(template);
  syncSettings();
  drawFields();
  updateOutput();
}

for (const [id, property] of Object.entries(settings)) {
  const element = $(id);
  element.addEventListener(element.tagName === "SELECT" ? "change" : "input", () => {
    currentForm[property] = element.value;
    updateOutput();
  });
}

$("form-template").addEventListener("change", event => resetToTemplate(event.target.value));

$("form-add-field").addEventListener("click", () => {
  try {
    currentForm = addField(currentForm, $("form-add-type").value);
    syncSettings();
    drawFields();
    updateOutput();
  } catch (error) { setStatus(error.message, true); }
});

$("form-copy").addEventListener("click", async () => {
  const markup = $("form-code").value;
  if (!markup) return;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(markup);
    } else {
      $("form-code").focus();
      $("form-code").select();
      if (!document.execCommand("copy")) throw new Error("Clipboard unavailable");
    }
    setStatus("Embed HTML copied. Include syntyr.core.css and configure your submission endpoint.");
  } catch {
    $("form-code").focus();
    $("form-code").select();
    setStatus("Clipboard permission unavailable; select and manually copy the HTML.", true);
  }
});

$("form-download").addEventListener("click", () => {
  try {
    const markup = exportStandalone(currentForm);
    const blob = new Blob([markup], { type: "text/html;charset=utf-8" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = "syntyr-form.html";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setStatus("HTML page downloaded. Place syntyr.core.css beside it and configure the endpoint.");
  } catch (error) { setStatus(error.message, true); }
});

resetToTemplate("contact");
