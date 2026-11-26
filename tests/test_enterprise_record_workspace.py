"""Grouped enterprise workspace contracts without a frontend runtime."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "examples/enterprise-record-workspace.html"


class Markup(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def values(fragment):
    """Visible monetary amounts must agree with machine-readable values."""
    amounts = re.findall(r'<data(?: id="[^"]+")? value="(\d+)">\$([\d,]+)(?: \([\d.]+%\))?</data>', fragment)
    result = []
    for raw, displayed in amounts:
        assert int(raw) == int(displayed.replace(",", "")), fragment
        result.append(int(raw))
    return result


class EnterpriseWorkspaceContract(unittest.TestCase):
    def setUp(self):
        self.html = PAGE.read_text()
        self.tags = Markup(self.html).tags

    def test_native_controls_and_unique_record_links(self):
        ids = [a["id"] for _, a in self.tags if "id" in a]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(any(t in ("script", "form") for t, _ in self.tags))
        self.assertFalse(any(k.startswith("on") for _, a in self.tags for k in a))
        self.assertFalse(any(a.get("role") in ("grid", "treegrid", "tablist") for _, a in self.tags))
        sheets = {a["id"] for t, a in self.tags if a.get("role") == "dialog" and "popover" in a}
        targets = [a["popovertarget"] for t, a in self.tags
                   if t == "button" and "popovertarget" in a]
        self.assertEqual(len(sheets), 6)
        self.assertEqual(set(targets), sheets)
        for sheet in sheets:
            self.assertEqual(targets.count(sheet), 3)  # opener, Close, Done
        for tag, a in self.tags:
            for k in ("aria-labelledby", "aria-describedby"):
                self.assertTrue(set(a.get(k, "").split()).issubset(ids))
            if tag == "a" and a.get("href", "").startswith("#"):
                self.assertIn(a["href"][1:], ids)

    def test_groups_subtotals_inspector_values_and_chart_reconcile(self):
        groups = re.findall(r'<details id="([^"]+)" class="syn-details" open>(.*?)</details>', self.html, re.S)
        self.assertEqual([name for name, _ in groups], ["booked", "review", "available"])
        sums = {}
        count = 0
        for group, html in groups:
            with self.subTest(group=group):
                body = html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
                footer = html.split("<tfoot>", 1)[1].split("</tfoot>", 1)[0]
                items = re.findall(r'<tr>(.*?)</tr>', body, re.S)
                amount = sum(values(body))
                sums[group] = amount
                count += len(items)
                self.assertEqual(values(footer), [amount])
                self.assertIn(f'{len(items)} records · ${amount:,}', html)
                for item in items:
                    target = re.search(r'popovertarget="([^"]+)"', item).group(1)
                    sheet = self.html.split(f'<div id="{target}"', 1)[1].split("</footer>", 1)[0]
                    self.assertEqual(values(sheet), values(item))
                    date = re.search(r'<time datetime="([^"]+)">', item).group(1)
                    self.assertIn(f'<time datetime="{date}">', sheet)
        total = sum(sums.values())
        self.assertIn(f'id="record-count">{count}</p>', self.html)
        self.assertIn(f'id="potential">${total:,}</p>', self.html)
        self.assertIn(f'id="grand-total" value="{total}">', self.html)
        self.assertIn(f'id="booked-amount">${sums["booked"]:,}</p>', self.html)
        self.assertIn('id="review-count">2</p>', self.html)
        bars = self.html.split('<ul class="syn-viz-bars">', 1)[1].split("</ul>", 1)[0]
        self.assertEqual(values(bars), list(sums.values()))
        shares = [float(p) for p in re.findall(r'--syn-viz-value:([\d.]+)', bars)]
        self.assertEqual(len(shares), len(sums))
        for amount, share in zip(sums.values(), shares):
            self.assertAlmostEqual(share, amount / total * 100, places=5)
            self.assertIn(f"({share:.1f}%)", bars)
        self.assertAlmostEqual(sum(shares), 100, places=5)

    def test_all_groups_are_semantic_and_allowlisted(self):
        self.assertEqual(sum(t == "table" for t, _ in self.tags), 3)
        self.assertEqual(sum(t == "caption" for t, _ in self.tags), 3)
        self.assertEqual(sum(t == "tfoot" for t, _ in self.tags), 3)
        self.assertEqual(sum(t == "th" and a.get("scope") == "col" for t, a in self.tags), 12)
        self.assertEqual(sum(t == "th" and a.get("scope") == "row" for t, a in self.tags), 9)
        self.assertEqual(sum(t == "div" and a.get("class") == "syn-table-wrap"
                             and a.get("tabindex") == "0" and a.get("aria-label")
                             is not None for t, a in self.tags), 3)
        for tag, attrs in self.tags:
            if tag == "link" and attrs.get("rel") == "stylesheet":
                self.assertTrue((PAGE.parent / attrs["href"]).is_file())
        for path in ("README.md", "docs/index.html", "docs/recipes.md", "llms.txt",
                     "scripts/build_cloudflare_site.py", "tests/axe_audit.py"):
            self.assertIn(PAGE.name, (ROOT / path).read_text(), path)


if __name__ == "__main__":
    unittest.main()
