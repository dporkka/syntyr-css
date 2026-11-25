"""Optional, dependency-free static HTML checks against the Syntyr CSS contract.

This is a development tool, not a CSS preprocessor or application dependency.
It validates only literal HTML attributes. Dynamic templates need their own
language-aware integration; false claims about rendered state are avoided.
"""
from __future__ import annotations

import argparse
from difflib import get_close_matches
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "metadata" / "syntyr-contract.json"
# HTMLParser does not synthesize end tags for void elements.
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})


def _stylesheet_name(href: str, names: set[str]) -> str | None:
    """Match a published Syntyr entrypoint, not an unrelated stylesheet."""
    path = urlsplit(href).path.replace("\\", "/")
    for name in sorted(names, key=len, reverse=True):
        if path == name or path.endswith("/" + name):
            return name
    return None


def _is_dynamic(value: str) -> bool:
    return any(char in value for char in "{}$<>")  # conservative template escape


class _SyntyrParser(HTMLParser):
    def __init__(self, contract: dict):
        super().__init__(convert_charrefs=True)
        self.classes = {c["name"]: c for c in contract["classes"]}
        self.attribute_values = contract["attributes"]
        self.stylesheet_names = set(contract["stylesheets"])
        self.linked_stylesheets: set[str] = set()
        self.used_classes: list[tuple[int, int, str]] = []
        self.unscoped_classes: list[tuple[int, int, str]] = []
        self.complete_document = False
        # (tag, known-root-ancestor, possible-dynamic-root-ancestor)
        self.scope_stack: list[tuple[str, bool, bool]] = []
        self.diagnostics: list[dict] = []

    def _error(self, code: str, message: str, line: int, column: int, **details):
        self.diagnostics.append({
            "line": line, "column": column + 1,
            "severity": "error", "code": code, "message": message,
            **details,
        })

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        data = dict(attrs)
        line, col = self.getpos()
        if tag == "html":
            self.complete_document = True
        class_values = [data.get(key) or "" for key in ("class", "classname")]
        local_root = any("syn-root" in value.split()
                         for value in class_values if not _is_dynamic(value))
        dynamic_scope = any(_is_dynamic(value) for value in class_values)
        parent_root = self.scope_stack[-1][1] if self.scope_stack else False
        parent_possible = self.scope_stack[-1][2] if self.scope_stack else False
        has_root = parent_root or local_root
        possibly_scoped = has_root or parent_possible or dynamic_scope
        if tag not in _VOID_TAGS:
            self.scope_stack.append((tag, has_root, possibly_scoped))
        # Inert <template> content may be cloned into an existing Syntyr root.
        within_template = any(frame[0] == "template" for frame in self.scope_stack)
        if tag == "link" and "stylesheet" in (data.get("rel") or "").split():
            name = _stylesheet_name(data.get("href") or "", self.stylesheet_names)
            if name:
                self.linked_stylesheets.add(name)
        for class_attr in ("class", "classname"):
            class_value = data.get(class_attr) or ""
            if _is_dynamic(class_value):
                continue  # template output cannot be resolved safely without its renderer
            for name in class_value.split():
                if not name.startswith("syn-"):
                    continue
                if name not in self.classes:
                    matches = get_close_matches(name, self.classes, n=3, cutoff=0.75)
                    suggestions = [
                        {"name": match, "stylesheets": sorted(self.classes[match]["stylesheets"])}
                        for match in matches
                    ]
                    self._error("unknown-class", f"Unknown Syntyr class '{name}'.",
                                line, col, suggestions=suggestions)
                else:
                    self.used_classes.append((line, col, name))
                    if name != "syn-root" and not possibly_scoped and not within_template:
                        self.unscoped_classes.append((line, col, name))
        for name, allowed in self.attribute_values.items():
            value = data.get(name)
            if value is not None and not _is_dynamic(value) and allowed and value not in allowed:
                self._error("invalid-attribute-value",
                            f"Invalid {name}='{value}'; expected one of: {', '.join(allowed)}.",
                            line, col, attribute=name, allowed_values=list(allowed))

    def handle_endtag(self, tag):
        # Drop any inner implicitly-unclosed tags alongside the closing tag.
        # Unmatched closing tags must not disturb the known scope.
        for index in range(len(self.scope_stack) - 1, -1, -1):
            if self.scope_stack[index][0] == tag.lower():
                del self.scope_stack[index:]
                break

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)


class _SemanticParser(HTMLParser):
    """Opt-in, conservative checks for literal native HTML, not a DOM/ARIA engine."""

    # Image submits need alt text; type=button needs a value or another name.
    _UNLABELED_INPUT_TYPES = frozenset(("hidden", "submit", "reset"))
    _LABELABLE_TAGS = frozenset(("button", "input", "meter", "output",
                                 "progress", "select", "textarea"))
    _DIALOG_COMMANDS = frozenset(("show-modal", "close", "request-close"))

    @classmethod
    def _is_labelable(cls, node):
        tag, attrs = node["tag"], node["attrs"]
        # Static HTML cannot tell whether a custom element is form-associated.
        if "-" in tag or "is" in attrs:
            return True
        return tag in cls._LABELABLE_TAGS and not (
            tag == "input" and (attrs.get("type") or "").lower() == "hidden")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        node = {"tag": tag, "attrs": dict(attrs), "parents": tuple(self.stack),
                "line": self.getpos()[0], "column": self.getpos()[1] + 1}
        if tag != "template" and not any(p["tag"] == "template" for p in self.stack):
            self.nodes.append(node)
        if tag not in _VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag.lower():
                del self.stack[i:]
                break

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    @staticmethod
    def _finding(node, code, message, severity="error"):
        return {"line": node["line"], "column": node["column"],
                "severity": severity, "code": code, "message": message}

    def findings(self, *, complete_document):
        result = []
        ids = {}
        labels = set()
        for node in self.nodes:
            attrs = node["attrs"]
            identifier = attrs.get("id") or ""
            if identifier and not _is_dynamic(identifier):
                if identifier in ids:
                    result.append(self._finding(node, "duplicate-id",
                                                f"Duplicate id='{identifier}'."))
                else:
                    ids[identifier] = node
            if node["tag"] == "label":
                target = attrs.get("for") or ""
                if target and not _is_dynamic(target):
                    labels.add(target)
        for node in self.nodes:
            tag, attrs = node["tag"], node["attrs"]
            identifier = attrs.get("id") or ""
            if tag == "summary" and (not node["parents"] or
                                     node["parents"][-1]["tag"] != "details"):
                result.append(self._finding(node, "summary-outside-details",
                    "summary must be a direct child of details to be an interactive disclosure."))
            if complete_document and tag == "input":
                target = attrs.get("list")
                if target is not None and not _is_dynamic(target):
                    destination = ids.get(target)
                    if destination is None:
                        result.append(self._finding(node, "missing-native-target",
                            f"input list='{target}' does not reference an element."))
                    elif destination["tag"] != "datalist":
                        result.append(self._finding(node, "invalid-datalist-target",
                            f"input list='{target}' must reference a datalist element."))
            if complete_document:
                # Target integrity is independent of the input's accessible name.
                # Exempt controls still need valid literal native invoker targets.
                for attr in ("popovertarget", "commandfor"):
                    target = attrs.get(attr)
                    if target is None or _is_dynamic(target):
                        continue
                    destination = ids.get(target)
                    if destination is None:
                        result.append(self._finding(node, "missing-native-target",
                            f"{attr} references missing id='{target}'."))
                    elif attr == "popovertarget" and "popover" not in destination["attrs"]:
                        result.append(self._finding(node, "invalid-popover-target",
                            f"popovertarget='{target}' must point to an element with a popover attribute."))
                    elif attr == "commandfor" and tag == "button":
                        # The HTML command keyword is ASCII case-insensitive.
                        command = (attrs.get("command") or "").lower()
                        if command in self._DIALOG_COMMANDS and destination["tag"] != "dialog":
                            result.append(self._finding(node, "invalid-dialog-target",
                                f"command='{command}' requires a dialog target."))
                        # Popover commands dispatch command events on any HTML
                        # target, even without a popover attribute. Do not flag.
            if tag in ("input", "textarea", "select"):
                input_type = (attrs.get("type") or "text").lower() if tag == "input" else ""
                # Hidden controls are absent from the accessibility tree; their
                # native ID references are still validated above.
                hidden = "hidden" in attrs or any(
                    "hidden" in parent["attrs"] for parent in node["parents"])
                dynamic_name = any(_is_dynamic(value) for value in (
                    identifier, attrs.get("aria-label") or "",
                    attrs.get("aria-labelledby") or ""))
                if not hidden and not dynamic_name and input_type not in self._UNLABELED_INPUT_TYPES:
                    wrapped = any(
                        parent["tag"] == "label" and (
                            not parent["attrs"].get("for") or
                            parent["attrs"].get("for") == identifier
                        ) for parent in node["parents"])
                    native_name = (
                        (attrs.get("alt") or "").strip() if input_type == "image" else
                        (attrs.get("value") or "").strip() if input_type == "button" else ""
                    )
                    named = wrapped or (identifier and identifier in labels) or native_name or (
                        attrs.get("aria-label") or "").strip() or (
                        attrs.get("aria-labelledby") or "").strip() or (
                        attrs.get("title") or "").strip()
                    if not named:
                        result.append(self._finding(node, "missing-form-label",
                                                    f"{tag} needs a visible label or accessible name."))
            if complete_document and tag == "label":
                target = attrs.get("for") or ""
                if target and not _is_dynamic(target):
                    destination = ids.get(target)
                    if destination is None:
                        result.append(self._finding(node, "missing-label-target",
                                                    f"label for='{target}' has no matching id."))
                    elif not self._is_labelable(destination):
                        result.append(self._finding(node, "invalid-label-target",
                            f"label for='{target}' does not reference a labelable element."))
            if complete_document:
                for attr in ("aria-labelledby", "aria-describedby"):
                    references = attrs.get(attr) or ""
                    if references and not _is_dynamic(references):
                        for target in references.split():
                            if target not in ids:
                                result.append(self._finding(node, "missing-aria-reference",
                                    f"{attr} references missing id='{target}'."))
            if tag == "tr" and attrs.get("aria-selected") is not None:
                table = next((p for p in reversed(node["parents"]) if p["tag"] == "table"), None)
                if table and table["attrs"].get("role") not in ("grid", "treegrid"):
                    result.append(self._finding(node, "aria-selected-static-table",
                        "Ordinary table rows cannot model interactive selection; use "
                        "data-syn-state for visual highlighting or implement a real grid.", "warning"))
            if tag == "table" and not attrs.get("aria-label") and not attrs.get("aria-labelledby"):
                descendants = [n for n in self.nodes if node in n["parents"]]
                if any(n["tag"] == "th" for n in descendants) and not any(
                        n["tag"] == "caption" for n in descendants):
                    result.append(self._finding(node, "table-missing-name",
                        "Data table has no caption or accessible name; consider a caption.", "warning"))
        return result


def validate_html(html: str, contract: dict, *, stylesheets: set[str] | None = None,
                  semantic: bool = False) -> list[dict]:
    """Return deterministic diagnostics for literal HTML.

    When no Syntyr stylesheet is linked and none is explicitly provided,
    treat input as a partial HTML fragment and skip module presence checks.
    """
    parser = _SyntyrParser(contract)
    parser.feed(html)
    parser.close()
    # A fragment may inherit .syn-root from its host, so only diagnose root
    # scope when the input explicitly contains a full HTML document.
    if parser.complete_document:
        for line, col, name in parser.unscoped_classes:
            parser._error("unscoped-class",
                          f"'{name}' is outside .syn-root; wrap it in a Syntyr root.",
                          line, col, class_name=name, required_root="syn-root")
    loaded = parser.linked_stylesheets if stylesheets is None else stylesheets
    # An explicit empty set means the caller knows no Syntyr CSS is loaded;
    # None with no recognized <link> means an unverifiable HTML fragment.
    if loaded or stylesheets is not None:
        for line, col, name in parser.used_classes:
            expected = set(parser.classes[name]["stylesheets"])
            if not expected.intersection(loaded):
                hint = ", ".join(sorted(expected, key=lambda n: (n.count("/"), len(n)))[:3])
                parser._error("missing-stylesheet",
                              f"'{name}' is not in the loaded Syntyr CSS; add {hint}.",
                              line, col, required_stylesheets=sorted(expected),
                              loaded_stylesheets=sorted(loaded))
    if semantic:
        inspector = _SemanticParser()
        inspector.feed(html)
        inspector.close()
        parser.diagnostics.extend(inspector.findings(complete_document=parser.complete_document))
    return sorted(parser.diagnostics, key=lambda d: (d["line"], d["column"],
                                                    d["code"] == "missing-stylesheet"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Validate literal Syntyr classes and states in HTML.")
    p.add_argument("files", nargs="+", type=Path,
                   help="Static HTML files to check; use - to read HTML from stdin.")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--semantic", action="store_true",
                   help="Additionally lint literal native HTML semantics (conservative; templates need rendered checks).")
    p.add_argument("--stylesheets", action="append", default=None,
                   help="Known loaded Syntyr stylesheets, comma-separated; overrides HTML links.")
    p.add_argument("--contract", type=Path, default=CONTRACT)
    args = p.parse_args(argv)
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        configured = None
        if args.stylesheets is not None:
            configured = set()
            for value in args.stylesheets:
                for item in value.split(","):
                    found = _stylesheet_name(item.strip(), set(contract["stylesheets"]))
                    if found is None:
                        p.error(f"Unrecognized Syntyr stylesheet: {item}")
                    configured.add(found)
        results = []
        for file in args.files:
            source = sys.stdin.read() if str(file) == "-" else file.read_text(encoding="utf-8")
            diagnostics = validate_html(source, contract, stylesheets=configured, semantic=args.semantic)
            label = "<stdin>" if str(file) == "-" else str(file)
            results += [{"file": label, **diag} for diag in diagnostics]
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print(f"syntyr check: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        for diag in results:
            print(f"{diag['file']}:{diag['line']}:{diag['column']}: "
                  f"{diag['severity']} [{diag['code']}]: {diag['message']}")
        if not results:
            print(f"OK: {len(args.files)} file(s) checked")
    return 1 if any(d["severity"] == "error" for d in results) else 0


if __name__ == "__main__":
    sys.exit(main())
