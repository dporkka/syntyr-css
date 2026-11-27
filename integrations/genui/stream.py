"""Bounded NDJSON framing for the host-owned A2UI session.

This is a transport adapter, not an A2UI network client. Hosts own the
authenticated stream, timeouts, cancellation, and session lifecycle.
"""
import json
from dataclasses import dataclass

from . import MAX_BYTES, GenUIError, _require

MAX_STREAM_BYTES = 8 * 1024 * 1024
MAX_MESSAGES = 1024


@dataclass(frozen=True)
class SurfaceUpdate:
    surface_id: str
    html: str | None


def iter_messages(chunks, *, max_stream_bytes=MAX_STREAM_BYTES,
                  max_messages=MAX_MESSAGES):
    """Yield complete UTF-8 LF/CRLF-delimited records from bounded byte chunks.

    Invalid framing terminates iteration. The final record must end in LF.
    Empty chunks are harmless; empty records and UTF-8 BOMs are rejected.
    """
    _require(type(max_stream_bytes) is int and
             0 < max_stream_bytes <= MAX_STREAM_BYTES, "Invalid stream byte limit")
    _require(type(max_messages) is int and
             0 < max_messages <= MAX_MESSAGES, "Invalid message limit")
    buffer = bytearray()
    total = count = 0
    for chunk in chunks:
        _require(type(chunk) is bytes and len(chunk) <= MAX_BYTES,
                 "Invalid stream chunk")
        total += len(chunk)
        _require(total <= max_stream_bytes, "Stream byte limit exceeded")
        start = 0
        while start < len(chunk):
            end = chunk.find(b"\n", start)
            stop = len(chunk) if end == -1 else end
            _require(len(buffer) + stop - start <= MAX_BYTES,
                     "Stream record size exceeded")
            buffer.extend(chunk[start:stop])
            if end == -1:
                break
            if buffer.endswith(b"\r"):
                del buffer[-1:]
            _require(buffer and not buffer.startswith(b"\xef\xbb\xbf"),
                     "Invalid stream record")
            try:
                message = buffer.decode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise GenUIError("Invalid stream UTF-8") from exc
            _require(bool(message.strip()), "Empty stream record")
            count += 1
            _require(count <= max_messages, "Stream message limit exceeded")
            buffer.clear()
            start = end + 1
            yield message
    _require(not buffer, "Truncated stream record")


def iter_surface_updates(chunks, session, *, max_stream_bytes=MAX_STREAM_BYTES,
                         max_messages=MAX_MESSAGES):
    """Apply each complete record and yield the validated surface result.

    Earlier accepted records remain committed if a later record fails.
    No later records are applied after an error or consumer cancellation.
    """
    for message in iter_messages(chunks, max_stream_bytes=max_stream_bytes,
                                 max_messages=max_messages):
        html = session.apply(message)
        # The session has validated the envelope and its single event.
        event = json.loads(message)
        kind = next(key for key in event if key != "version")
        yield SurfaceUpdate(event[kind]["surfaceId"], html)
