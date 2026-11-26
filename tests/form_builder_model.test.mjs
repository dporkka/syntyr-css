import test from "node:test";
import assert from "node:assert/strict";
import {
  FORM_SCHEMA, FIELD_TYPES, createForm, addField, moveField,
  validateForm, renderForm, exportStandalone
} from "../docs/form-builder-model.mjs";

test("creates native, named, labeled contact fields from a known template", () => {
  const form = createForm("contact");
  assert.equal(form.schema, FORM_SCHEMA);
  assert.equal(form.method, "post");
  assert.ok(form.fields.some(field => field.type === "email" && field.required));
  const html = renderForm(form);
  assert.match(html, /<form[^>]+method="post"/);
  assert.match(html, /<label[^>]+for="syn-field-/);
  assert.match(html, /<input[^>]+type="email"[^>]+required/);
  assert.match(html, /<button[^>]+type="submit"/);
  assert.doesNotMatch(html, /<script|onclick=|onsubmit=/i);
});

test("renders help, native constraints and an accessible textarea", () => {
  const form = createForm("contact");
  const message = form.fields.find(field => field.type === "textarea");
  message.help = "Tell us what you need";
  const html = renderForm(form);
  assert.match(html, /aria-describedby="syn-help-/);
  assert.match(html, /<p class="syn-help" id="syn-help-/);
  assert.match(html, /<textarea[^>]+required/);
  assert.match(html, /Tell us what you need/);
});

test("scopes control and help IDs to each exported form", () => {
  const ids = new Set();
  for (const template of ["contact", "newsletter", "contact"]) {
    const form = createForm(template);
    form.fields.find(item => item.name === "email").help = "Use your work email";
    const html = renderForm(form);
    assert.ok(exportStandalone(form).includes(html));
    const localIds = new Set(Array.from(html.matchAll(/ id="([^"]+)"/g), match => match[1]));
    for (const id of localIds) {
      assert.ok(!ids.has(id), "Duplicate ID across forms: " + id);
      ids.add(id);
    }
    const email = html.match(/<input[^>]+name="email"[^>]*>/)[0];
    const [, controlId] = email.match(/ id="([^"]+)"/);
    const [, helpId] = email.match(/ aria-describedby="([^"]+)"/);
    assert.ok(html.includes('for="' + controlId + '"'));
    assert.ok(html.includes('<p class="syn-help" id="' + helpId + '"'));
    assert.ok(localIds.has(controlId) && localIds.has(helpId));
  }
});

test("escapes hostile text and rejects unsafe endpoint protocols", () => {
  const form = createForm("contact");
  form.title = '<img src=x onerror="alert(1)">';
  form.fields[0].label = 'Name" autofocus onfocus="alert(1)';
  form.fields[0].placeholder = "<script>alert(1)</script>";
  const html = renderForm(form);
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/);
  assert.doesNotMatch(html, /<img|<script|"\s+autofocus/i);
  form.action = "javascript:alert(1)";
  assert.throws(() => renderForm(form), /action/i);
  form.action = "//attacker.example/collect";
  assert.throws(() => renderForm(form), /action/i);
});

test("rejects duplicate names, unknown types and missing accessible labels", () => {
  const form = createForm("contact");
  form.fields[1].name = form.fields[0].name;
  assert.throws(() => validateForm(form), /duplicate/i);
  form.fields[1].name = "other_name";
  form.fields[1].type = "html";
  assert.throws(() => validateForm(form), /type/i);
  form.fields[1].type = "email";
  form.fields[1].label = " ";
  assert.throws(() => validateForm(form), /label/i);
});

test("renders select and radio options using native controls and grouping", () => {
  const form = createForm("blank");
  form.fields = [
    { id: "role", type: "select", name: "role", label: "Role", required: true, help: "", options: ["Engineer", "Designer"] },
    { id: "plan", type: "radio", name: "plan", label: "Plan", required: true, help: "", options: ["Basic", "Plus"] },
    { id: "accept", type: "checkbox", name: "accept", label: "Accept terms", required: true, help: "" }
  ];
  const html = renderForm(form);
  assert.match(html, /<select[^>]*required/);
  assert.match(html, /<option value="">Choose an option<\/option>/);
  assert.match(html, /<fieldset/);
  assert.match(html, /<legend[^>]*>Plan<\/legend>/);
  assert.match(html, /<input[^>]+type="radio"[^>]+value="Basic"[^>]+required/);
  assert.match(html, /type="checkbox"/);
});

test("POST file uploads require multipart encoding and cannot use GET", () => {
  const form = createForm("blank");
  form.fields = [{ id: "resume", name: "resume", label: "Resume", type: "file", required: true, help: "" }];
  const html = renderForm(form);
  assert.match(html, /enctype="multipart\/form-data"/);
  form.method = "get";
  assert.throws(() => renderForm(form), /file|post/i);
});

test("adds and moves fields without mutating original form", () => {
  const original = createForm("contact");
  const added = addField(original, "tel");
  assert.equal(added.fields.length, original.fields.length + 1);
  assert.equal(added.fields.at(-1).type, "tel");
  assert.ok(FIELD_TYPES.includes("tel"));
  const reordered = moveField(added, added.fields.length - 1, 0);
  assert.equal(reordered.fields[0].type, "tel");
  assert.equal(added.fields[0].type, original.fields[0].type);
});

test("standalone export includes local CSS and works without JavaScript", () => {
  const form = createForm("feedback");
  const html = exportStandalone(form);
  assert.match(html, /^<!doctype html>/i);
  assert.match(html, /href="syntyr.core.css"/);
  assert.match(html, /class="syn-root syn-page"/);
  assert.doesNotMatch(html, /<script|<iframe|onsubmit=/i);
});

test("rejects unsupported shapes, empty endpoints and excessive fields", () => {
  const form = createForm("contact");
  form.action = "";
  assert.throws(() => validateForm(form), /action/i);
  form.action = "/contact";
  form.fields[0].name = "a bad name";
  assert.throws(() => validateForm(form), /name/i);
  form.fields[0].name = "full_name";
  form.fields = Array.from({ length: 51 }, (_, index) => ({
    id: "f" + index, name: "f" + index, type: "text", label: "Field " + index
  }));
  assert.throws(() => validateForm(form), /50|many/i);
});

test("requires HTTPS or an explicit loopback HTTP development endpoint", () => {
  const form = createForm("contact");
  for (const action of [
    "http://example.test/contact", "http://localhost.example.test/contact",
    "http://localhost@evil.example/contact", "http://2130706433/contact",
    "https://user:pass@example.test/contact", "https:///example.test",
    "https://example.test:99999", "/\\evil.example/collect",
    "https://example.test/\u0001", "https://example.test/\u007fmore"
  ]) {
    form.action = action;
    assert.throws(() => renderForm(form), /action/i, action);
    assert.throws(() => exportStandalone(form), /action/i, action);
  }
  for (const action of ["/contact", "./contact", "../contact",
    "https://example.test/contact?source=form", "http://localhost:3000/contact",
    "http://127.0.0.1:8080/contact", "http://[::1]:8080/contact"]) {
    form.action = action;
    assert.equal(validateForm(form).action, action);
    assert.doesNotThrow(() => exportStandalone(form));
  }
});
