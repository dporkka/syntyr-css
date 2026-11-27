"""Opt-in real Chromium DOM parity/security smoke test; no package install."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integrations.genui import render_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", required=True, help="Existing sandbox-capable Chromium executable")
    args = parser.parse_args()
    integration = ROOT / "integrations/genui"
    example = (integration / "example.json").read_text(encoding="utf-8")
    source = (integration / "browser.mjs").read_text(encoding="utf-8")
    css = (ROOT / "dist/syntyr.core.css").read_text(encoding="utf-8")
    # Only repository-owned code and fixture are embedded into this local test.
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>GenUI browser smoke</title><style>' + css + '</style>'
            '<main id="host"></main><div id="reference" hidden>' +
            render_json(example) + '</div><output id="result">PENDING</output>'
            '<script type="module">' + source + '\nconst fixture=' +
            json.dumps(example).replace("<", "\\u003c") + ';\n' + """
const host=document.getElementById('host');
const result=document.getElementById('result');
const checks={};
try {
  const root=mountJson(host,fixture);
  checks.parity=root.isEqualNode(document.getElementById('reference').firstElementChild);
  checks.css=getComputedStyle(root.querySelector('.syn-stack')).display==='grid';
  checks.progress=root.querySelector('progress').labels.length===1;
  checks.table=root.querySelectorAll('th[scope=col]').length===2;
  const region=root.querySelector('[role=region]');
  region.focus(); checks.focus=document.activeElement===region;
  const details=root.querySelector('details');
  details.querySelector('summary').click(); checks.disclosure=details.open;
  host.style.width='375px';
  checks.narrow=host.scrollWidth<=host.clientWidth;
  host.style.width='900px';
  checks.wide=host.scrollWidth<=host.clientWidth;
  const payload='<img src=x onerror=alert(1)>';
  const malicious=JSON.stringify({version:1,root:{type:'Text',props:{text:payload}}});
  const safe=mountJson(host,malicious);
  checks.inert=safe.textContent===payload&&!safe.querySelector('img');
  try { mountJson(host,'{"version":1,"root":{"type":"Script"}}'); checks.rollback=false; }
  catch(e) { checks.rollback=e instanceof GenUIError&&host.firstChild===safe; }
} catch(e) { checks.error=String(e); }
result.textContent=JSON.stringify(checks);
</script></html>""")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.html"
        path.write_text(html, encoding="utf-8")
        proc = subprocess.run([
            args.chromium, "--headless", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", "--window-size=1280,900",
            "--user-data-dir=" + str(Path(tmp) / "profile"),
            "--dump-dom", path.as_uri(),
        ], capture_output=True, text=True, timeout=30, check=True)
        match = re.search(r'<output id="result">([^<]+)</output>', proc.stdout)
        if not match:
            raise RuntimeError("Browser produced no test result")
        checks = json.loads(match[1])
        print(json.dumps(checks, indent=2))
        if len(checks) != 10 or not all(value is True for value in checks.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
