"""Optional Chromium computed-style smoke; does not change the zero-JS example."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    chrome = os.environ["SYNTYR_CHROMIUM_BIN"]
    example = (ROOT / "examples/data-grid.html").read_text()
    script = r"""
<script>
try {
  const viewport = document.querySelector('.syn-data-grid__viewport');
  viewport.style.inlineSize = '240px';
  const header = document.querySelector('.syn-data-grid__columnheader[data-syn-pin]');
  const cell = document.querySelector('.syn-data-grid__cell[data-syn-pin]');
  const range = document.querySelector('[data-syn-range]');
  const conflict = document.querySelector('[data-syn-conflict]');
  const check = (condition, label) => { if (!condition) throw Error(label); };
  check(getComputedStyle(header).position === 'sticky', 'header sticky');
  check(getComputedStyle(cell).position === 'sticky', 'cell sticky');
  const opaque = item => {
    const color = getComputedStyle(item).backgroundColor;
    return /^rgb\(/.test(color) || /^rgba\([^,]+,[^,]+,[^,]+,\s*1\)$/.test(color);
  };
  check(opaque(cell), 'opaque cell');
  for (const state of ['data-syn-range', 'data-syn-selected', 'data-syn-focused']) {
    cell.setAttribute(state, 'true');
    check(opaque(cell), 'opaque pinned ' + state);
    cell.removeAttribute(state);
  }
  check(getComputedStyle(conflict).borderBlockEndStyle === 'dashed', 'conflict marker');
  check(getComputedStyle(range).backgroundColor !== 'rgba(0, 0, 0, 0)', 'range background');
  for (const direction of ['ltr', 'rtl']) {
    viewport.dir = direction;
    viewport.scrollLeft = direction === 'ltr' ? 100 : -100;
    check(Math.abs(viewport.scrollLeft) > 30, direction + ' scroll');
    const v = viewport.getBoundingClientRect();
    for (const item of [header, cell]) {
      const b = item.getBoundingClientRect();
      const start = v.left + viewport.clientLeft;
      const end = start + viewport.clientWidth;
      check(Math.abs(direction === 'ltr' ? b.left-start : b.right-end) < 3,
        direction + ' pinned edge');
    }
  }
  document.body.setAttribute('data-grid-test', 'PASS');
} catch (error) { document.body.setAttribute('data-grid-test', 'FAIL: ' + error.message); }
</script>
"""
    # Absolute file URL for the canonical generated CSS; the checked-in example stays script-free.
    source = example.replace("../dist/", (ROOT / "dist").as_uri() + "/")
    source = source.replace("</body>", script + "</body>")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "grid.html"
        page.write_text(source)
        result = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-first-run",
                                 "--window-size=320,800", "--dump-dom", page.as_uri()],
                                capture_output=True, text=True, timeout=30)
        if result.returncode or 'data-grid-test="PASS"' not in result.stdout:
            marker = next((line for line in result.stdout.splitlines() if "data-grid-test=" in line), "")
            raise SystemExit(f"Chromium grid smoke failed: {marker}\n{result.stderr[-1500:]}")
    print("PASS: Chromium grid pinning (LTR/RTL), opaque cells, range and conflict states")

if __name__ == "__main__":
    main()
