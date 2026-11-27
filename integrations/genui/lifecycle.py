"""Bounded, host-owned A2UI snapshot sessions; no transport or side effects."""

import json

from . import MAX_BYTES, MAX_NODES, GenUIError, _invalid_constant, _pairs, _require
from .a2ui import BASIC_CATALOG_ID, _identifier, render_a2ui
from .bindings import resolve_components, update_model, validate_model

MAX_ACTIVE = 8
MAX_CREATED = 128


class SurfaceSession:
    """One synchronous session per trusted host conversation.

    Each accepted create/update returns complete HTML. Delete returns None.
    A rejected event never changes the previously accepted surface.
    """

    def __init__(self, *, max_active=MAX_ACTIVE, max_created=MAX_CREATED):
        _require(type(max_active) is int and type(max_created) is int
                 and 1 <= max_active <= MAX_ACTIVE
                 and 1 <= max_created <= MAX_CREATED, "Invalid session capacity")
        self._max_active = max_active
        self._max_created = max_created
        self._surfaces = {}
        self._created = set()

    def html(self, surface_id):
        _identifier(surface_id)
        _require(surface_id in self._surfaces, "Unknown surface")
        return self._surfaces[surface_id][1]

    def apply(self, document):
        _require(type(document) is str and len(document) <= MAX_BYTES, "Invalid event size")
        try:
            _require(len(document.encode("utf-8")) <= MAX_BYTES, "Invalid event size")
            event = json.loads(document, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
        except (ValueError, RecursionError, UnicodeError) as exc:
            raise GenUIError("Invalid event JSON") from exc
        _require(type(event) is dict and len(event) == 2
                 and event.get("version") == "1.0", "Expected A2UI 1.0 event")
        kind = next(key for key in event if key != "version")
        payload = event[kind]
        fields = {
            "createSurface": {"surfaceId", "catalogId", "components"},
            "updateComponents": {"surfaceId", "components"},
            "deleteSurface": {"surfaceId"},
            "updateDataModel": {"surfaceId", "value"},
        }
        optional = {"createSurface": {"dataModel"}, "updateDataModel": {"path"}}
        _require(kind in fields and type(payload) is dict
                 and fields[kind] <= set(payload) <= fields[kind] | optional.get(kind, set()),
                 "Unsupported event")
        sid = _identifier(payload["surfaceId"])
        if kind == "deleteSurface":
            _require(sid in self._surfaces, "Unknown surface")
            del self._surfaces[sid]
            return None

        if kind == "createSurface":
            _require(sid not in self._created, "Surface ID already used")
            _require(len(self._surfaces) < self._max_active
                     and len(self._created) < self._max_created, "Session capacity exceeded")
            _require(payload["catalogId"] == BASIC_CATALOG_ID, "Unsupported catalog")
            proposed = {}
            model = payload.get("dataModel", {})
            validate_model(model)
        else:
            _require(sid in self._surfaces, "Unknown surface")
            proposed = self._surfaces[sid][0].copy()
            model = self._surfaces[sid][2]

        if kind == "updateDataModel":
            model = update_model(model, payload.get("path", "/"), payload["value"])
        else:
            changes = payload["components"]
            _require(type(changes) is list and 1 <= len(changes) <= MAX_NODES,
                     "Invalid component list")
            seen = set()
            for component in changes:
                _require(type(component) is dict and "id" in component, "Invalid component")
                cid = _identifier(component["id"])
                _require(cid not in seen, "Duplicate component ID in event")
                seen.add(cid)
                proposed[cid] = component

        _require(len(proposed) <= MAX_NODES, "Component count exceeded")
        # Validate the entire merged graph, including its cumulative byte budget.
        # Serialize with ASCII escaping to ensure lone surrogates remain invalid
        # input to the snapshot validator, rather than failing at the encoder.
        envelope = {
            "version": "1.0",
            "createSurface": {
                "surfaceId": sid, "catalogId": BASIC_CATALOG_ID,
                "components": list(proposed.values()), "dataModel": model,
            },
        }
        # Bound the stored model and unresolved graph together before resolving.
        snapshot = json.dumps(envelope, ensure_ascii=True, separators=(",", ":"))
        _require(len(snapshot) <= MAX_BYTES, "Cumulative snapshot size exceeded")
        surface = envelope["createSurface"]
        del surface["dataModel"]
        surface["components"] = resolve_components(surface["components"], model)
        html = render_a2ui(json.dumps(envelope, ensure_ascii=True, separators=(",", ":")))
        self._surfaces[sid] = (proposed, html, model)
        self._created.add(sid)
        return html
