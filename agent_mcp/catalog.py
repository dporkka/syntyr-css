"""Version-pinned public Syntyr catalog, using checked-in distribution artifacts.

The CSS files and curated metadata are the source of truth. No network,
authentication, writes, generated HTML, or invented component names.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from scripts.syntyr_check import _is_dynamic, _stylesheet_name, validate_html
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "0.3.0-alpha.4"
CANDIDATE = "0.3.0-alpha.5"
RELEASES = (PUBLISHED, CANDIDATE)
MAX_HTML_CHARS = 20_000
MAX_LOCAL_DOCUMENT_CHARS = 256 * 1024
MAX_RESULTS = 40

SELECTOR = re.compile(r"\.(syn-[a-zA-Z0-9_-]+)(?![a-zA-Z0-9_-])")
TOKEN = re.compile(r"(?<![\w-])(--syn-[a-zA-Z0-9_-]+)\s*:")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
PREFER = (
    "syntyr.core.css", "syntyr.recipes.css", "syntyr.semantic.css",
    "syntyr.semantic-bundle.css",
    "syntyr.geometry.css", "syntyr.effects.css", "syntyr.viz.css",
    "syntyr.utilities.css", "syntyr.motion.css", "syntyr.symbols.css",
    "syntyr.native-recipes.css", "syntyr.server.css", "syntyr.print.css",
    "syntyr.css", "syntyr.all.css", "headless/interactions.css",
)


class CatalogError(ValueError):
    """A caller requested a nonexistent or unsupported public API."""


class ClassExtractor(HTMLParser):
    """Collect only literal Syntyr classes and linked known CSS entrypoints."""

    def __init__(self, stylesheet_names: set[str]):
        super().__init__(convert_charrefs=True)
        self.names: set[str] = set()
        self.linked_stylesheets: set[str] = set()
        self.stylesheet_names = stylesheet_names

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag.lower() == "link" and "stylesheet" in (data.get("rel") or "").split():
            name = _stylesheet_name(data.get("href") or "", self.stylesheet_names)
            if name:
                self.linked_stylesheets.add(name)
        for key in ("class", "classname"):
            value = data.get(key) or ""
            if not _is_dynamic(value):
                self.names.update(name for name in value.split() if name.startswith("syn-"))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


class SyntyrCatalog:
    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.component_data = json.loads((self.root / "metadata/components.json").read_text())
        self.api_data = json.loads((self.root / "metadata/syntyr-api.json").read_text())
        if self.component_data["source_version"] != CANDIDATE:
            raise RuntimeError("Syntyr component catalog version needs review")
        if (self.root / "VERSION").read_text().strip() != CANDIDATE:
            raise RuntimeError("Syntyr candidate metadata differs from source VERSION")
        self._cache = {}

    def _release(self, release: str):
        if release not in RELEASES:
            raise CatalogError(f"Unsupported release {release!r}; choose {PUBLISHED} (published) or {CANDIDATE} (unreleased candidate)")
        return {
            "release": release,
            "release_status": "published" if release == PUBLISHED else "unreleased_candidate",
            "curated_catalog": True,
        }

    def _directory(self, release: str):
        return self.root / ("site-releases/" + PUBLISHED if release == PUBLISHED else "dist")

    def _catalog(self, release: str):
        self._release(release)
        if release in self._cache:
            return self._cache[release]
        directory = self._directory(release)
        found = {}
        for file in directory.glob("syntyr*.css"):
            if file.name in PREFER:
                # Sources are checked-in release artifacts, not transitive runtime APIs.
                src = CSS_COMMENT.sub("", file.read_text(encoding="utf-8"))
                found[file.name] = {
                    "classes": set(SELECTOR.findall(src)),
                    "tokens": set(TOKEN.findall(src)),
                }
        if release == CANDIDATE:
            adapter = self.root / "integrations/headless/interactions.css"
            src = CSS_COMMENT.sub("", adapter.read_text(encoding="utf-8"))
            found["headless/interactions.css"] = {
                "classes": set(SELECTOR.findall(src)),
                "tokens": set(TOKEN.findall(src)),
            }
        if "syntyr.core.css" not in found:
            raise RuntimeError(f"Missing checked-in core stylesheet for {release}")
        classes = set().union(*(v["classes"] for v in found.values()))
        tokens = set().union(*(v["tokens"] for v in found.values()))
        info = {"files": found, "classes": classes, "tokens": tokens}
        self._cache[release] = info
        return info

    def _stylesheet(self, name: str, kind: str, release: str):
        for file in PREFER:
            info = self._catalog(release)["files"].get(file)
            if info and name in info["classes" if kind == "class" else "tokens"]:
                return file
        return None

    def search_components(self, query: str = "", release: str = PUBLISHED):
        info = self._catalog(release)
        base = self._release(release)
        term = query.strip().casefold()
        matches = []
        for component in self.component_data["components"]:
            # Curated alpha.5 components may contain classes absent from alpha.4.
            if any(cls not in info["classes"] for cls in component["classes"]):
                continue
            if term not in (component["name"] + " " + component["notes"] + " " + " ".join(component["classes"])).casefold():
                continue
            matches.append({
                "name": component["name"],
                "classes": component["classes"],
                "stylesheets": sorted({
                    self._stylesheet(cls, "class", release)
                    for cls in component["classes"]
                }),
                "notes": component["notes"],
            })
        return {**base, "components": matches[:MAX_RESULTS],
                "note": "Curated examples only, not a complete class inventory."}

    def get_component(self, name: str, release: str = PUBLISHED):
        base = self._release(release)
        component = next((entry for entry in self.component_data["components"]
                          if entry["name"].casefold() == name.strip().casefold()), None)
        if component is None:
            raise CatalogError(f"Unknown component {name!r}; use search_components")
        info = self._catalog(release)
        missing = [cls for cls in component["classes"] if cls not in info["classes"]]
        if missing:
            raise CatalogError(f"Component {name!r} is unavailable in {release}: {', '.join(missing)}")
        return {**base, "component": {
            **component, "stylesheets": sorted({
                self._stylesheet(cls, "class", release) for cls in component["classes"]
            }),
        }, "note": "Syntyr styles native HTML; it does not implement app behavior."}

    def get_interaction_contracts(self, name: str = "", release: str = PUBLISHED):
        """Describe candidate-only UI anatomy and behavior ownership; never execute."""
        base = self._release(release)
        if release != CANDIDATE:
            raise CatalogError("Interaction contracts are unavailable in the published release; select the source candidate explicitly")
        manifest = json.loads((self.root / "metadata/interaction-contracts.v1.json").read_text(encoding="utf-8"))
        if manifest["source_version"] != release or manifest["schema_version"] != 1:
            raise RuntimeError("Interaction contract metadata version needs review")
        term = name.strip().casefold()
        contracts = [c for c in manifest["contracts"] if not term or c["id"] == term]
        if not contracts:
            raise CatalogError(f"Unknown interaction contract {name!r}; list contracts without a name")
        return {**base, "schema_version": manifest["schema_version"],
                "contracts": contracts, "note": manifest["note"]}

    def get_interaction_recipes(self, contract: str = "", release: str = PUBLISHED):
        """Discover runnable recipe references, not executable actions or test results."""
        contracts = self.get_interaction_contracts(contract, release)
        selected = {item["id"] for item in contracts["contracts"]}
        all_ids = {item["id"] for item in self.get_interaction_contracts("", release)["contracts"]}
        manifest = json.loads((self.root / "metadata/interaction-recipes.json").read_text(encoding="utf-8"))
        if (manifest["schema_version"] != 1 or manifest["source_version"] != release
                or manifest["release_status"] != "unreleased-source-candidate"):
            raise RuntimeError("Interaction recipe metadata version needs review")
        # A recipe may be a fallback or an alternative, not a conforming implementation.
        links = {
            "native-select": [("combobox", "fallback")],
            "native-popover": [("dropdown", "implementation")],
            "native-modal-dialog": [("dialog", "implementation"), ("disclosure", "example")],
            "native-table": [("sortable-table", "fallback")],
            "radix-menu": [("dropdown", "alternative")],
            "react-aria-combobox": [("combobox", "implementation")],
            "react-aria-sortable-grid": [("sortable-table", "implementation")],
            "radix-toast": [],
        }
        recipes = manifest["recipes"]
        if len(recipes) != len(links) or {item["id"] for item in recipes} != set(links):
            raise RuntimeError("Interaction recipe links need review")
        if {name for pairs in links.values() for name, _ in pairs} != all_ids:
            raise RuntimeError("Interaction contract links need review")
        known = self._catalog(release)["files"]
        result = []
        for item in recipes:
            relations = links[item["id"]]
            if contract.strip() and not any(name in selected for name, _ in relations):
                continue
            stylesheets = sorted({path.removeprefix("dist/").removeprefix("integrations/")
                                  for path in item["css"]})
            if not set(stylesheets) <= set(known):
                raise RuntimeError(f"Recipe stylesheet inventory needs review: {item['id']}")
            result.append({**item, "stylesheets": stylesheets,
                           "contract_links": [{"id": name, "relationship": relation}
                                              for name, relation in relations]})
        return {**self._release(release), "schema_version": manifest["schema_version"],
                "recipes": result,
                "note": "Recipe and test source references, not runtime actions, test results or accessibility certification."}

    def validate_composition(self, section_ids: list[str], interactions: list[dict],
                             stylesheets: list[str], runtime_policy: str = "scriptless",
                             release: str = PUBLISHED):
        """Preflight a declared candidate plan; does not render, execute or certify."""
        base = self._release(release)
        if release != CANDIDATE:
            raise CatalogError("Composition preflight requires the source candidate")
        if runtime_policy not in ("scriptless", "host-enabled"):
            raise CatalogError("Unknown runtime policy; choose scriptless or host-enabled")

        def strings(value, label, limit=100):
            if (not isinstance(value, list) or len(value) > limit
                    or not all(isinstance(v, str) and 0 < len(v) <= 128 for v in value)):
                raise CatalogError(f"{label} must be a bounded list of identifiers")
            return value

        strings(section_ids, "section_ids")
        strings(stylesheets, "stylesheets")
        known = set(self._catalog(release)["files"])
        if set(stylesheets) - known:
            raise CatalogError("Unknown stylesheet(s): " + ", ".join(sorted(set(stylesheets) - known)))
        if not isinstance(interactions, list) or len(interactions) > 100:
            raise CatalogError("interactions must be a bounded list of declarations")
        if not section_ids and not interactions:
            raise CatalogError("Composition requires at least one section or interaction")
        for entry in interactions:
            if (not isinstance(entry, dict)
                    or not {"contract", "recipe", "relationship"} <= entry.keys()
                    or entry.keys() - {"contract", "recipe", "relationship", "intentions", "state_hooks"}):
                raise CatalogError("Invalid interaction declaration fields")
            strings([entry["contract"], entry["recipe"], entry["relationship"]], "interaction identifiers")
            if entry["relationship"] not in ("implementation", "alternative", "fallback", "example"):
                raise CatalogError("Unknown recipe relationship")
            strings(entry.get("intentions", []), "intentions", 40)
            strings(entry.get("state_hooks", []), "state_hooks", 40)

        manifest = json.loads((self.root / "metadata/section-composer.v1.json").read_text(encoding="utf-8"))
        if (manifest["schema_version"] != 1 or manifest["source_version"] != release
                or manifest["runtime_requirement"] != "none"):
            raise RuntimeError("Section composer metadata needs review")
        sections = {item["id"]: item for item in manifest["sections"]}
        contracts = {item["id"]: item for item in self.get_interaction_contracts("", release)["contracts"]}
        recipes = {item["id"]: item for item in self.get_interaction_recipes("", release)["recipes"]}
        required = set()
        diagnostics = []

        def issue(code, field, value):
            diagnostics.append({"code": code, "field": field, "value": value})

        for i, ident in enumerate(section_ids):
            if ident not in sections:
                issue("unknown-section", f"section_ids[{i}]", ident)
            else:
                required.update(sections[ident]["required_stylesheets"])

        for i, entry in enumerate(interactions):
            field = f"interactions[{i}]"
            contract = contracts.get(entry["contract"])
            recipe = recipes.get(entry["recipe"])
            if contract is None:
                issue("unknown-contract", field + ".contract", entry["contract"])
            if recipe is None:
                issue("unknown-recipe", field + ".recipe", entry["recipe"])
            if contract is None or recipe is None:
                continue
            relation = {"id": contract["id"], "relationship": entry["relationship"]}
            if relation not in recipe["contract_links"]:
                issue("recipe-relationship-mismatch", field + ".relationship", entry["relationship"])
            required.update(recipe["stylesheets"])
            if runtime_policy == "scriptless" and recipe["kind"] != "native":
                issue("host-recipe-not-allowed", field + ".recipe", recipe["id"])
            intentions = entry.get("intentions", [])
            hooks = entry.get("state_hooks", [])
            if entry["relationship"] == "implementation":
                required.update(contract["stylesheets"])
                for intent in sorted(set(intentions) - set(contract["intentions"])):
                    issue("unknown-intention", field + ".intentions", intent)
                for hook in sorted(set(hooks) - set(contract["state_hooks"])):
                    issue("unknown-state-hook", field + ".state_hooks", hook)
            elif intentions or hooks:
                issue("unverified-interaction-claims", field, recipe["id"])

        if required - known:
            raise RuntimeError("Composition stylesheet inventory needs review")
        missing = sorted(required - set(stylesheets))
        for css in missing:
            issue("missing-stylesheet", "stylesheets", css)
        return {**base, "valid": not diagnostics, "runtime_policy": runtime_policy,
                "section_ids": list(section_ids), "required_stylesheets": sorted(required),
                "missing_stylesheets": missing, "diagnostics": diagnostics,
                "note": ("Declared plan only. Stylesheet requirements are exact catalog identifiers, "
                         "not inferred bundle coverage. Scriptless excludes headless recipes, "
                         "not server behavior. Does not inspect rendered HTML, validate live state "
                         "values, execute interactions, or certify accessibility.")}

    def lookup_api(self, name: str, release: str = PUBLISHED):
        base = self._release(release)
        kind = "class" if name.startswith("syn-") else "token" if name.startswith("--syn-") else None
        if not kind:
            raise CatalogError("Only syn-* class selectors or --syn-* custom properties are supported")
        info = self._catalog(release)
        if name not in info[kind + "es" if kind == "class" else "tokens"]:
            raise CatalogError(f"Unknown {kind} {name!r} for release {release}")
        metadata = next((entry for entry in self.api_data["classes" if kind == "class" else "tokens"]
                         if entry["name"] == name), None)
        stylesheet = self._stylesheet(name, kind, release)
        return {**base, "entry": {
            "name": name, "kind": kind, "stylesheet": stylesheet,
            "description": metadata["description"] if metadata and release == CANDIDATE else f"Syntyr {kind} ({stylesheet}); see version-pinned CSS and docs.",
        }}

    def get_theme_tokens(self, query: str = "", release: str = PUBLISHED):
        info = self._catalog(release)
        base = self._release(release)
        themes = ["grid", "noir", "studio"] if release == PUBLISHED else [
            t for t in self.api_data["themes"] if t != "auto"
        ]
        tokens = []
        for name in sorted(info["tokens"]):
            if query.strip().casefold() not in name.casefold():
                continue
            tokens.append(self.lookup_api(name, release)["entry"])
            if len(tokens) >= MAX_RESULTS:
                break
        return {**base, "themes": themes, "tokens": tokens,
                "note": "Names and stylesheets only, not computed browser values. Results capped at 40."}

    def _validation_contract(self, release: str) -> dict:
        """Assemble the shared HTML validator contract from this release's CSS.

        The source candidate's HTML states are not silently assumed to be
        available in the published immutable alpha.4 release.
        """
        info = self._catalog(release)
        classes = [
            {"name": name, "stylesheets": sorted(
                file for file, data in info["files"].items() if name in data["classes"]
            )}
            for name in sorted(info["classes"])
        ]
        if release == PUBLISHED:
            attributes = {"data-syn-theme": ["grid", "noir", "studio"]}
        else:
            source_contract = json.loads((self.root / "metadata/syntyr-contract.json").read_text())
            if source_contract.get("source_version") != release:
                raise RuntimeError("Candidate validator metadata version differs from installed CSS")
            attributes = source_contract["attributes"]
        return {"classes": classes, "attributes": attributes,
                "stylesheets": sorted(info["files"])}

    def validate_markup(self, html: str, release: str = PUBLISHED,
                        stylesheets: list[str] | None = None):
        return self._validate_markup(html, release, stylesheets, MAX_HTML_CHARS)

    def validate_local_document(self, html: str, release: str = PUBLISHED,
                                stylesheets: list[str] | None = None):
        """Bounded local authoring path; intentionally not an MCP tool."""
        return self._validate_markup(html, release, stylesheets, MAX_LOCAL_DOCUMENT_CHARS)

    def _validate_markup(self, html, release, stylesheets, limit):
        base = self._release(release)
        if not isinstance(html, str) or len(html) > limit:
            raise CatalogError(f"HTML is too long or invalid (limit {limit} characters)")
        info = self._catalog(release)
        if not isinstance(stylesheets, (list, type(None))) or not all(isinstance(s, str) for s in (stylesheets or [])):
            raise CatalogError("stylesheets must be an array of known Syntyr stylesheet identifiers")
        invalid = sorted(set(stylesheets or []) - set(info["files"]))
        if invalid:
            raise CatalogError(f"Unknown stylesheet(s) in {release}: {', '.join(invalid)}")

        extractor = ClassExtractor(set(info["files"]))
        extractor.feed(html)
        extractor.close()
        provided = sorted(set(stylesheets) if stylesheets is not None else extractor.linked_stylesheets)
        contract = self._validation_contract(release)
        diagnostics = validate_html(html, contract,
                                    stylesheets=set(provided) if stylesheets is not None else None)
        found = sorted(extractor.names)
        known = [c for c in found if c in info["classes"]]
        missing = [c for c in found if c not in info["classes"]]
        loaded = set().union(*(info["files"][f]["classes"] for f in provided)) if provided else set()
        required = sorted({self._stylesheet(c, "class", release) for c in known if c not in loaded})
        return {**base, "classes_checked": known, "unknown_classes": missing,
                "missing_stylesheets": required, "installed_stylesheets": provided,
                "diagnostics": diagnostics,
                "note": ("Literal HTML class and release-aware state checks, not a WCAG or "
                         "runtime audit. Missing stylesheet summaries with no linked/explicit "
                         "CSS are recommendations; module diagnostics require CSS context.")}
