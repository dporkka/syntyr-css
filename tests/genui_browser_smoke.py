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

  const changed=JSON.parse(fixture);
  changed.root.children[1].props.text='Updated report';
  changed.root.children[3].children[2].props.rows[0][1]='Complete';
  region.focus();
  const updated=reconcileJson(host,JSON.stringify(changed));
  checks.sameRoot=updated===root;
  checks.preservedFocus=document.activeElement===region&&updated.querySelector('[role=region]')===region;
  checks.preservedDisclosure=updated.querySelector('details')===details&&details.open;
  checks.updated=updated.textContent.includes('Updated report')&&region.querySelector('td:nth-child(2)').textContent==='Complete';
  const tree=(order)=>JSON.stringify({version:1,root:{type:'Stack',children:order.map(label=>({type:'Details',props:{summary:label},children:[{type:'Text',props:{text:label}}]}))}});
  const keysA=new Map([['root/0','a'],['root/1','b']]);
  const keysB=new Map([['root/0','b'],['root/1','a']]);
  const a=reconcileJson(host,tree(['Alpha','Beta']),{keys:keysA}).querySelector('details');
  a.open=true; a.querySelector('summary').focus();
  const reordered=reconcileJson(host,tree(['Beta','Alpha']),{keys:keysB});
  checks.keyedMove=reordered.querySelectorAll('details')[1]===a&&a.open&&document.activeElement===a.querySelector('summary');
  const before=host.firstChild;
  try { reconcileJson(host,tree(['Beta','Alpha']),{keys:new Map([['root/0','a'],['root/1','a']])}); checks.badKeys=false; }
  catch(e) { checks.badKeys=e instanceof GenUIError&&host.firstChild===before; }
  try { reconcileJson(host,tree(['Beta','Alpha']),{keys:new Map([['root/9','unused']])}); checks.unknownKey=false; }
  catch(e) { checks.unknownKey=e instanceof GenUIError&&host.firstChild===before; }
  const replaced=reconcileJson(host,tree(['Beta','New']),{keys:new Map([['root/0','b'],['root/1','new']])});
  checks.noStateLeak=replaced.querySelectorAll('details')[1]!==a&&!replaced.querySelectorAll('details')[1].open;

  const columns=Array.from({length:20},(_,i)=>'Column '+i);
  const tableSnapshot=(value)=>JSON.stringify({version:1,root:{type:'Table',props:{caption:'Wide report',columns,rows:[columns.map(()=>value)]}}});
  host.style.width='220px';
  const wide=reconcileJson(host,tableSnapshot('Before')).querySelector('[role=region]');
  wide.scrollLeft=50;
  const offset=wide.scrollLeft;
  const wideUpdated=reconcileJson(host,tableSnapshot('After')).querySelector('[role=region]');
  checks.preservedScroll=offset>0&&wideUpdated===wide&&wideUpdated.scrollLeft===offset;
  try { reconcileJson(host,'{"version":1,"root":{"type":"Script"}}'); checks.reconcileRollback=false; }
  catch(e) { checks.reconcileRollback=e instanceof GenUIError&&host.querySelector('[role=region]')===wide&&wide.scrollLeft===offset; }
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
        if len(checks) != 20 or not all(value is True for value in checks.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
