import json
import unittest

from integrations.genui import GenUIError
from integrations.genui.a2ui import BASIC_CATALOG_ID
from integrations.genui.lifecycle import SurfaceSession


def event(kind, sid="demo", **props):
    return json.dumps({"version": "1.0", kind: {"surfaceId": sid, **props}})


def create(sid="demo", text="Before"):
    return event("createSurface", sid, catalogId=BASIC_CATALOG_ID,
                 components=[{"id": "root", "component": "Column", "children": ["text"]},
                             {"id": "text", "component": "Text", "text": text}])


def update(text, sid="demo"):
    return event("updateComponents", sid, components=[
        {"id": "text", "component": "Text", "text": text}])


class SurfaceSessionTests(unittest.TestCase):
    def test_create_update_delete(self):
        s = SurfaceSession()
        self.assertIn("Before", s.apply(create()))
        self.assertIn("After", s.apply(update("After")))
        self.assertNotIn("Before", s.html("demo"))
        self.assertIsNone(s.apply(event("deleteSurface")))
        with self.assertRaises(GenUIError):
            s.html("demo")
        with self.assertRaises(GenUIError):
            s.apply(create())

    def test_invalid_updates_are_atomic(self):
        s = SurfaceSession()
        original = s.apply(create())
        for components in [
            [{"id": "text", "component": "Button", "action": "pay"}],
            [{"id": "root", "component": "Column", "children": ["missing"]}],
            [{"id": "text", "component": "Text", "text": "A"},
             {"id": "text", "component": "Text", "text": "B"}],
            [{"id": "root", "component": "Column", "children": ["root"]}],
            [{"id": "orphan", "component": "Text", "text": "orphan"}],
        ]:
            with self.subTest(components=components), self.assertRaises(GenUIError):
                s.apply(event("updateComponents", components=components))
            self.assertEqual(original, s.html("demo"))
        self.assertIn("&lt;script&gt;", s.apply(update("<script>")))

    def test_surfaces_are_isolated_and_unknown_messages_fail(self):
        s = SurfaceSession()
        s.apply(create("a", "Alpha"))
        s.apply(create("b", "Beta"))
        s.apply(update("New", "a"))
        self.assertIn("Beta", s.html("b"))
        for bad in [create("a"), update("Unknown", "c"),
                    event("deleteSurface", "c"),
                    event("updateDataModel", "a", value={"x": 1}),
                    event("deleteSurface", "a", extra=True)]:
            with self.assertRaises(GenUIError):
                s.apply(bad)
        self.assertIn("New", s.html("a"))

    def test_lifetime_and_active_capacity(self):
        s = SurfaceSession(max_active=1, max_created=2)
        s.apply(create("a"))
        with self.assertRaises(GenUIError):
            s.apply(create("b"))
        s.apply(event("deleteSurface", "a"))
        s.apply(create("b"))
        s.apply(event("deleteSurface", "b"))
        with self.assertRaises(GenUIError):
            s.apply(create("c"))

    def test_incremental_addition_and_cumulative_limits(self):
        s = SurfaceSession()
        s.apply(create())
        html = s.apply(event("updateComponents", components=[
            {"id": "root", "component": "Column", "children": ["text", "new"]},
            {"id": "new", "component": "Text", "text": "New"}]))
        self.assertIn("New", html)
        old = s.html("demo")
        many = [{"id": str(i), "component": "Text", "text": "x"*4000} for i in range(40)]
        s.apply(event("updateComponents", components=[
            {"id": "root", "component": "Column", "children": ["text", "new"]+[str(i) for i in range(40)]},
            *many]))
        before = s.html("demo")
        more = [{"id": str(i), "component": "Text", "text": "x"*4000} for i in range(40, 80)]
        with self.assertRaises(GenUIError):
            s.apply(event("updateComponents", components=[
                {"id": "root", "component": "Column", "children": ["text", "new"]+[str(i) for i in range(80)]},
                *more]))
        self.assertEqual(before, s.html("demo"))
        self.assertNotEqual(old, before)

    def test_duplicate_keys_and_bad_versions(self):
        s = SurfaceSession()
        for bad in ['{"version":"1.0","version":"1.0","deleteSurface":{}}',
                    '{"version":"0.9","deleteSurface":{"surfaceId":"demo"}}',
                    " " * 262145]:
            with self.assertRaises(GenUIError):
                s.apply(bad)
