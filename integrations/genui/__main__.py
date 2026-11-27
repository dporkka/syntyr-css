"""Read a JSON specification from stdin; emit validated HTML to stdout."""
import sys

from . import MAX_BYTES, GenUIError, render_json


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise GenUIError("Invalid document size")
        html = render_json(raw.decode("utf-8"))
    except (GenUIError, UnicodeError):
        print("Invalid GenUI specification", file=sys.stderr)
        return 2
    print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
