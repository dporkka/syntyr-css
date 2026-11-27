import json
import unittest

from integrations.genui import GenUIError
from integrations.genui.a2ui import BASIC_CATALOG_ID
from integrations.genui.lifecycle import SurfaceSession


def event(kind, sid="a", **props):
    return json.dumps({"version": "1.0", kind: {"surfaceId": sid, **props}})


def create(sid="a", model=None, path="/report/status"):
    return event("createSurface", sid, catalogId=BASIC_CATALOG_ID,
                 components=[{"id": "root", "component": "Text", "text": {"@path": path}}],
                 dataModel=model if model is not None else {"report": {"status": "Before"}})


class BindingTests(unittest.TestCase):
    def test_initial_and_incremental_text(self):
        s = SurfaceSession()
        self.assertIn("Before", s.apply(create()))
        self.assertIn("&lt;script&gt;", s.apply(event("updateDataModel", path="/report/status", value="<script>")))
        self.assertNotIn("Before", s.html("a"))
        self.assertIn("Replaced", s.apply(event("updateDataModel", value={"report": {"status": "Replaced"}})))

    def test_pointer_escaping(self):
        s = SurfaceSession()
        self.assertIn("Escaped", s.apply(create(model={"a/b": {"~key": "Escaped"}}, path="/a~1b/~0key")))
        self.assertIn("Changed", s.apply(event("updateDataModel", path="/a~1b/~0key", value="Changed")))

    def test_invalid_update_preserves_old_model_and_html(self):
        s = SurfaceSession()
        original = s.apply(create())
        for props in [
            {"path": "/report/status", "value": None},
            {"path": "/report/status", "value": {"not": "string"}},
            {"path": "/report/status", "value": 123},
            {"path": "/report/status", "value": "x"*4001},
            {"path": "/missing/status", "value": "no"},
            {"path": "/report/~2status", "value": "no"},
            {"path": "/__proto__", "value": "no"},
            {"value": {"other": "no"}},
        ]:
            with self.subTest(props=props), self.assertRaises(GenUIError):
                s.apply(event("updateDataModel", **props))
            self.assertEqual(original, s.html("a"))
        self.assertIn("Before", s.apply(event("updateComponents", components=[
            {"id": "root", "component": "Text", "text": {"@path": "/report/status"}}])))

    def test_model_isolated_per_surface(self):
        s = SurfaceSession()
        s.apply(create("a"))
        s.apply(create("b", {"report": {"status": "Beta"}}))
        s.apply(event("updateDataModel", "a", path="/report/status", value="Alpha"))
        self.assertIn("Beta", s.html("b"))

    def test_rejects_unsupported_bindings_and_model(self):
        for path in ["report/status", "/", "/report/~", "/report/status/child", "/constructor"]:
            with self.subTest(path=path), self.assertRaises(GenUIError):
                SurfaceSession().apply(create(path=path))
        for model in [{"report": ["x"]}, {"report": {"status": "ok"}, "__proto__": "bad"}]:
            with self.assertRaises(GenUIError):
                SurfaceSession().apply(create(model=model))
        with self.assertRaises(GenUIError):
            SurfaceSession().apply(event("createSurface", catalogId=BASIC_CATALOG_ID,
                dataModel={}, components=[{"id":"root", "component":"Text", "text":{"@call":"run"}}]))

    def test_unreferenced_add_delete_and_root_slash(self):
        s = SurfaceSession()
        s.apply(create())
        s.apply(event("updateDataModel", path="/other", value="Extra"))
        s.apply(event("updateDataModel", path="/other", value=None))
        self.assertIn("New", s.apply(event("updateDataModel", path="/", value={"report":{"status":"New"}})))

    def test_combined_snapshot_budget(self):
        s = SurfaceSession()
        original = s.apply(create())
        first = {str(i): "x"*4000 for i in range(40)}
        s.apply(event("updateDataModel", path="/extra", value=first))
        with self.assertRaises(GenUIError):
            s.apply(event("updateDataModel", path="/more", value=first))
        self.assertEqual(original, s.html("a"))
