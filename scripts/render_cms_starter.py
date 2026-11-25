"""Render portable CMS JSON into static Syntyr HTML, using only the Python stdlib.

The CMS is an editor, never a runtime dependency. Strictly validate the small
page contract before rendering; JSON from Git is still untrusted content.
"""
from __future__ import annotations

import argparse
from html import escape
import json
import re
from pathlib import Path
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "examples/cms-starter"
DESTINATION = STARTER / "_site"
THEMES = frozenset(("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"))
SECTION_FIELDS = {
    "hero": {"type", "id", "eyebrow", "heading", "description", "button"},
    "features": {"type", "id", "heading", "items"},
    "pricing": {"type", "id", "heading", "plans"},
    "faq": {"type", "id", "heading", "items"},
    "cta": {"type", "id", "heading", "description", "button"},
}


def _object(value: object, fields: set[str], required: set[str], path: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    missing = required - value.keys()
    extra = value.keys() - fields
    if missing or extra:
        raise ValueError(f"{path}: missing {sorted(missing)}, unexpected {sorted(extra)}")
    return value


def _text(value: object, path: str, limit: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValueError(f"{path}: expected non-empty text up to {limit} chars")
    return escape(value, quote=True)


def _url(value: object, path: str) -> str:
    if not isinstance(value, str) or len(value) > 2048 or not value:
        raise ValueError(f"{path}: invalid URL")
    if any(c.isspace() or c == "\\" or ord(c) < 32 for c in value):
        raise ValueError(f"{path}: unsafe URL")
    if value.startswith("/") and not value.startswith("//"):
        return escape(value, quote=True)
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"{path}: only root-relative or absolute HTTP(S) URLs allowed")
    return escape(value, quote=True)


def _button(value: object, path: str) -> dict[str, str]:
    button = _object(value, {"label", "url"}, {"label", "url"}, path)
    return {"label": _text(button["label"], f"{path}.label", 100),
            "url": _url(button["url"], f"{path}.url")}


def _items(value: object, path: str, max_items: int = 24) -> list:
    if not isinstance(value, list) or not 1 <= len(value) <= max_items:
        raise ValueError(f"{path}: expected 1 to {max_items} items")
    return value


def validate_document(document: object) -> dict:
    """Validate all input, including nested content that templates do not inspect."""
    page = _object(document, {"title", "description", "theme", "sections"},
                   {"title", "description", "theme", "sections"}, "page")
    _text(page["title"], "page.title", 180)
    _text(page["description"], "page.description", 500)
    if not isinstance(page["theme"], str) or page["theme"] not in THEMES:
        raise ValueError("page.theme: unsupported theme")
    sections = _items(page["sections"], "page.sections")
    if not isinstance(sections[0], dict) or sections[0].get("type") != "hero":
        raise ValueError("page.sections: the first section must be a hero with the page h1")
    used_ids = set()
    for index, section in enumerate(sections):
        path = f"page.sections[{index}]"
        if not isinstance(section, dict) or not isinstance(section.get("type"), str) or section["type"] not in SECTION_FIELDS:
            raise ValueError(f"{path}.type: unsupported section type")
        kind = section["type"]
        fields = SECTION_FIELDS[kind]
        _object(section, fields, fields, path)
        section_id = section["id"]
        if not isinstance(section_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", section_id):
            raise ValueError(f"{path}.id: expected stable lowercase slug")
        if section_id in used_ids:
            raise ValueError(f"{path}.id: duplicate section identifier")
        used_ids.add(section_id)
        _text(section["heading"], f"{path}.heading", 180)
        if kind in ("hero", "cta"):
            _text(section["description"], f"{path}.description", 500)
            _button(section["button"], f"{path}.button")
        if kind == "hero":
            _text(section["eyebrow"], f"{path}.eyebrow", 120)
        if kind in ("features", "faq"):
            item_fields = {"title", "description"} if kind == "features" else {"question", "answer"}
            for item_index, item in enumerate(_items(section["items"], f"{path}.items")):
                item_path = f"{path}.items[{item_index}]"
                _object(item, item_fields, item_fields, item_path)
                for field in item_fields:
                    _text(item[field], f"{item_path}.{field}", 1000)
        if kind == "pricing":
            for plan_index, plan in enumerate(_items(section["plans"], f"{path}.plans", 6)):
                plan_path = f"{path}.plans[{plan_index}]"
                _object(plan, {"name", "price", "features", "button"},
                        {"name", "price", "features", "button"}, plan_path)
                _text(plan["name"], f"{plan_path}.name", 100)
                _text(plan["price"], f"{plan_path}.price", 100)
                _button(plan["button"], f"{plan_path}.button")
                for feature_index, feature in enumerate(_items(plan["features"], f"{plan_path}.features")):
                    _text(feature, f"{plan_path}.features[{feature_index}]", 200)
    return page


def _render_section(section: dict, index: int) -> str:
    kind = section["type"]
    label_id = f"section-{section['id']}"
    heading = _text(section["heading"], "heading", 180)
    heading_tag = "h1" if index == 0 else "h2"
    head = f'<{heading_tag} id="{label_id}" class="syn-heading">{heading}</{heading_tag}>'
    if kind == "hero":
        button = _button(section["button"], "button")
        return (f'<section class="syn-region" aria-labelledby="{label_id}"><div class="syn-site-hero">'
                f'<p class="syn-eyebrow">{_text(section["eyebrow"], "eyebrow")}</p>'
                f'<{heading_tag} id="{label_id}" class="syn-site-heading">{heading}</{heading_tag}>'
                f'<p class="syn-lede">{_text(section["description"], "description")}</p>'
                f'<div class="syn-actions"><a class="syn-button syn-button--primary" href="{button["url"]}">{button["label"]}</a></div>'
                '</div></section>')
    if kind == "features":
        cards = "".join(
            f'<article class="syn-feature-card"><h3>{_text(item["title"], "feature.title")}</h3>'
            f'<p>{_text(item["description"], "feature.description")}</p></article>'
            for item in section["items"]
        )
        return f'<section class="syn-region" aria-labelledby="{label_id}">{head}<div class="syn-feature-grid">{cards}</div></section>'
    if kind == "pricing":
        plans = []
        for plan in section["plans"]:
            button = _button(plan["button"], "plan.button")
            features = "".join(f"<li>{_text(feature, 'feature')}</li>" for feature in plan["features"])
            plans.append(
                f'<article class="syn-price-card"><h3>{_text(plan["name"], "plan.name")}</h3>'
                f'<p class="syn-price-value">{_text(plan["price"], "plan.price")}</p>'
                f'<ul class="syn-feature-list">{features}</ul>'
                f'<a class="syn-button syn-button--primary" href="{button["url"]}">{button["label"]}</a></article>'
            )
        return f'<section class="syn-region" aria-labelledby="{label_id}">{head}<div class="syn-pricing">{"".join(plans)}</div></section>'
    if kind == "faq":
        details = "".join(
            f'<details class="syn-panel"><summary>{_text(item["question"], "faq.question")}</summary>'
            f'<p>{_text(item["answer"], "faq.answer")}</p></details>'
            for item in section["items"]
        )
        return f'<section class="syn-region" aria-labelledby="{label_id}">{head}<div class="syn-stack">{details}</div></section>'
    if kind == "cta":
        button = _button(section["button"], "button")
        return (f'<section class="syn-region syn-panel" aria-labelledby="{label_id}">{head}'
                f'<p class="syn-lede">{_text(section["description"], "description")}</p>'
                f'<a class="syn-button syn-button--primary" href="{button["url"]}">{button["label"]}</a></section>')
    raise ValueError(f"unsupported section type {kind}")


def render_document(document: object) -> str:
    page = validate_document(document)
    title = _text(page["title"], "title", 180)
    description = _text(page["description"], "description", 500)
    theme = page["theme"]
    sections = "\n".join(_render_section(section, index) for index, section in enumerate(page["sections"]))
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <title>{title}</title>
  <link rel="stylesheet" href="/css/syntyr.core.css">
  <link rel="stylesheet" href="/css/syntyr.recipes.css">
</head>
<body class="syn-root" data-syn-theme="{theme}">
  <a href="#content">Skip to content</a>
  <header class="syn-region"><nav aria-label="Primary"><a href="/">Home</a></nav></header>
  <main id="content" class="syn-shell">
{sections}
  </main>
  <footer class="syn-region"><p class="syn-muted">{title}</p></footer>
</body>
</html>
'''


def build(source: Path = STARTER, destination: Path = DESTINATION, css_root: Path = ROOT / "dist") -> None:
    """Write one static site plus optional Sveltia admin; editor runs only at /admin."""
    page = json.loads((source / "content/pages/home.json").read_text(encoding="utf-8"))
    markup = render_document(page)  # Validate before writing any output.
    destination.mkdir(parents=True, exist_ok=True)
    css_dir = destination / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    for name in ("syntyr.core.css", "syntyr.recipes.css"):
        shutil.copyfile(css_root / name, css_dir / name)
    admin = destination / "admin"
    admin.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "config.yml"):
        shutil.copyfile(source / "admin" / name, admin / name)
    (destination / "index.html").write_text(markup, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=STARTER, help="Root of the CMS starter repository")
    parser.add_argument("--css-root", type=Path, default=ROOT / "dist", help="Directory with built Syntyr CSS")
    parser.add_argument("--output", type=Path, default=DESTINATION)
    args = parser.parse_args()
    build(source=args.source, destination=args.output, css_root=args.css_root)
    print(f"Built Syntyr CMS starter at {args.output}")
