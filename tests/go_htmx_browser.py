"""Optional browser smoke for native, JavaScript-free Go form submission.

Run from repository root with Go and Playwright browsers installed:
python tests/go_htmx_browser.py
"""
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples/go-htmx"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def check():
    port = free_port()
    url = f"http://127.0.0.1:{port}/contacts"
    with tempfile.TemporaryDirectory(prefix="syntyr-go-smoke-") as temp_dir:
        # Launch the binary itself, not 'go run', whose compiler subprocess may
        # survive termination and leave the test HTTP listener running.
        binary = Path(temp_dir) / "syntyr-go-demo"
        subprocess.run(["go", "build", "-o", str(binary), "."],
                       cwd=DEMO, check=True, timeout=90)
        proc = subprocess.Popen(
            [str(binary), "-addr", f"127.0.0.1:{port}"],
            cwd=DEMO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError(f"Go server exited with {proc.returncode}")
                try:
                    with urllib.request.urlopen(url, timeout=0.3) as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("Go server did not start")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 390, "height": 844})
                    page.goto(url)
                    assert page.locator("script").count() == 0
                    page.get_by_role("searchbox", name="Find a contact").fill("Ada")
                    page.get_by_role("button", name="Search").click()
                    page.wait_for_url("**/contacts?q=Ada")
                    assert page.get_by_role("status").inner_text() == "1 contact found."
                    assert page.get_by_role("row", name="Ada Lovelace Analytical Works ada@example.test").count() == 1
                    assert page.get_by_role("row", name="Grace Hopper Compiler Labs grace@example.test").count() == 0
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    print("PASS Go native GET: submit, escaped HTML, filtered results, narrow viewport")
                finally:
                    browser.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
            # Verify the listening process is gone, including on failing tests.
            with socket.socket() as probe:
                assert probe.connect_ex(("127.0.0.1", port)) != 0, (
                    f"Go test server still listening on port {port}"
                )


if __name__ == "__main__":
    check()
