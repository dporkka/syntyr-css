import json
import unittest

from integrations.genui import GenUIError, MAX_BYTES
from integrations.genui.a2ui import BASIC_CATALOG_ID
from integrations.genui.lifecycle import SurfaceSession
from integrations.genui.stream import iter_messages, iter_surface_updates


def frame(kind, sid="a", **payload):
    return json.dumps({"version": "1.0", kind: {"surfaceId": sid, **payload}},
                      ensure_ascii=False).encode("utf-8") + b"\n"


def create(sid="a"):
    return frame("createSurface", sid, catalogId=BASIC_CATALOG_ID,
                 dataModel={"status": "Café"},
                 components=[{"id": "root", "component": "Text",
                              "text": {"@path": "/status"}}])


def update(value, sid="a"):
    return frame("updateDataModel", sid, path="/status", value=value)


class StreamTests(unittest.TestCase):
    def test_chunk_boundaries_and_split_utf8(self):
        wire = create() + update("Prêt") + frame("deleteSurface")
        session = SurfaceSession()
        results = list(iter_surface_updates((wire[i:i+1] for i in range(len(wire))), session))
        self.assertEqual([r.surface_id for r in results], ["a", "a", "a"])
        self.assertIn("Café", results[0].html)
        self.assertIn("Prêt", results[1].html)
        self.assertIsNone(results[2].html)
        with self.assertRaises(GenUIError):
            session.html("a")

    def test_multiple_frames_and_crlf(self):
        wire = create().replace(b"\n", b"\r\n") + update("Olá")
        self.assertEqual(len(list(iter_messages([b"", wire, b""]))), 2)

    def test_truncated_tail_is_not_applied(self):
        s = SurfaceSession()
        with self.assertRaises(GenUIError):
            list(iter_surface_updates([create(), update("Lost")[:-1]], s))
        self.assertIn("Café", s.html("a"))

    def test_bad_event_terminates_without_applying_later_events(self):
        s = SurfaceSession()
        stream = iter_surface_updates([create() + update(123) + update("Never")], s)
        self.assertIn("Café", next(stream).html)
        with self.assertRaises(GenUIError):
            next(stream)
        self.assertIn("Café", s.html("a"))
        self.assertEqual(list(stream), [])

    def test_invalid_utf8_blank_and_bom(self):
        for invalid in [b"\xff\n", b"\n", b" \r\n", b"\xef\xbb\xbf{}\n"]:
            with self.subTest(invalid=invalid), self.assertRaises(GenUIError):
                list(iter_messages([invalid]))

    def test_oversized_record_and_chunk(self):
        for chunks in [[b"x"*MAX_BYTES, b"x"], [b"x"*(MAX_BYTES+1)]]:
            with self.subTest(lengths=[len(c) for c in chunks]), self.assertRaises(GenUIError):
                list(iter_messages(chunks))

    def test_total_and_count_limits(self):
        with self.assertRaises(GenUIError):
            list(iter_messages([b"{}\n", b"{}\n"], max_stream_bytes=5))
        with self.assertRaises(GenUIError):
            list(iter_messages([b"{}\n{}\n"], max_messages=1))

    def test_no_prefetch_and_surface_routing(self):
        s = SurfaceSession()
        def source():
            yield create("a")
            yield create("b")
            raise AssertionError("unexpected prefetch")
        stream = iter_surface_updates(source(), s)
        self.assertEqual(next(stream).surface_id, "a")
        with self.assertRaises(GenUIError):
            s.html("b")
        self.assertEqual(next(stream).surface_id, "b")
        stream.close()

    def test_invalid_limit_and_chunk_types(self):
        for kwargs in [{"max_messages": True}, {"max_messages": 0},
                       {"max_stream_bytes": 0}, {"max_stream_bytes": 10**9}]:
            with self.assertRaises(GenUIError):
                list(iter_messages([], **kwargs))
        with self.assertRaises(GenUIError):
            list(iter_messages(["{}\n"]))
