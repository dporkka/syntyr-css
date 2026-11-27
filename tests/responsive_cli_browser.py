"""Real local server smoke for the optional CLI (developer-only Playwright)."""
import json
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "good.html").write_text('<!doctype html><meta name="viewport" content="width=device-width"><button style="min-height:32px;min-width:32px">OK</button>')
        (root / "bad.html").write_text('<!doctype html><meta name="viewport" content="width=device-width"><button style="width:2200px;height:40px">Overflow</button>')
        server = ThreadingHTTPServer(("127.0.0.1",0), partial(SimpleHTTPRequestHandler,directory=folder))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for name, code in (("good.html",0),("bad.html",1)):
                result = subprocess.run([sys.executable, str(ROOT/"scripts/syntyr_agent.py"), "responsive",
                                         f"http://127.0.0.1:{server.server_port}/{name}"],
                                        text=True, capture_output=True, timeout=90)
                assert result.returncode == code, result.stderr + result.stdout
                report = json.loads(result.stdout)
                assert len(report["cases"]) == 6, report
                assert report["summary"]["pass" if code == 0 else "fail"] == 6, report
            print("PASS local CLI: six good cases, six intentionally failing cases")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    main()
