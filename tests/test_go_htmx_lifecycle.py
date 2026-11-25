"""Go browser smoke launches the compiled binary so cleanup owns the listener."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserProcessLifecycle(unittest.TestCase):
    def test_server_launches_directly_and_checks_listener_cleanup(self):
        source = (ROOT / "tests/go_htmx_browser.py").read_text()
        self.assertIn("TemporaryDirectory", source)
        self.assertIn('"go", "build"', source)
        self.assertNotIn('"go", "run"', source)
        self.assertIn("connect_ex", source)


if __name__ == "__main__":
    unittest.main()
