"""Developer-only triage of axe inconclusive color-contrast *elements*.

This is screenshot pixel sampling, not a WCAG conformance checker. It can
miss glyph-level gradient extrema, overlays, compositing, interactive states,
scroll positions and assistive-technology issues. Never auto-close axe findings
from this report. No CSS framework runtime dependencies are introduced.

Example (install playwright + Pillow in a disposable developer environment):
  python tests/axe_audit.py --axe-file /tmp/axe.min.js --report /tmp/axe.json
  python tests/contrast_pixel_triage.py --axe-report /tmp/axe.json \\
    --output /tmp/syntyr-contrast-triage.json
"""
import argparse
from collections import Counter
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COLOR = re.compile(r'^rgba?\(\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})(?:[ ,/]+([\d.]+))?\s*\)$')
REINSPECT_STATUSES = {"unsampled", "sampled_below_threshold", "narrow_margin",
                      "computed_placeholder_below_threshold"}


def parse_rgb(css: str):
    match = COLOR.fullmatch(css.strip())
    if not match:
        return None
    r, g, b = (int(part) for part in match.group(1, 2, 3))
    if any(not 0 <= channel <= 255 for channel in (r, g, b)):
        return None
    alpha = match.group(4)
    if alpha and float(alpha) < 0.99999:
        return None  # Requires explicit alpha compositing; don't guess.
    return (r, g, b)


def luminance(rgb):
    channels = [(x / 255 / 12.92 if x / 255 <= 0.04045 else
                 ((x / 255 + 0.055) / 1.055) ** 2.4) for x in rgb]
    return sum(x * weight for x, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(foreground, background):
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def text_contrast_threshold(font_size: float, weight: int):
    return 3.0 if font_size >= 24 or (font_size >= 18.66 and weight >= 700) else 4.5


def status_counts(items):
    return dict(sorted(Counter(item['status'] for item in items).items()))


def reinspection_targets(axe_report, prior, widths, pages=None):
    """Revisit only flagged observations that match the original axe targets."""
    def key(item):
        return item['page'], tuple(item['selector']), item['failure_summary']

    known = {key(dict(item, page=row['page']))
             for row in axe_report['pages'] for item in row['incomplete']
             if item['rule'] == 'color-contrast'}
    targets = []
    for item in prior['observations']:
        if item['status'] not in REINSPECT_STATUSES or item['viewport_width'] not in widths:
            continue
        if pages and item['page'] not in pages:
            continue
        if key(item) not in known:
            raise ValueError(f"Previous observation missing from axe report: {key(item)}")
        targets.append(item)
    return targets


def load_review_page(page, path, report):
    page.goto((ROOT / path).as_uri(), wait_until='load')
    # Older reports predate the explicit release-mode field and used the
    # default frozen catalog stylesheet.
    if path == 'docs/catalog.html' and report.get('catalog_release') == 'source-alpha5':
        from axe_audit import prepare_source_catalog
        prepare_source_catalog(page)


def reinspect(browser, report, prior, widths, pages):
    """Reveal one reachable target at a time; capture a viewport, not a full page."""
    from PIL import Image
    results = []
    for item in reinspection_targets(report, prior, widths, pages):
        width = item['viewport_width']
        result = {k: item[k] for k in ('page', 'selector', 'failure_summary', 'viewport_width')}
        result.update(status='unsampled', prior_status=item['status'])
        if 'reason' in item:
            result['prior_reason'] = item['reason']
        page = browser.new_page(viewport={'width': width, 'height': 900}, device_scale_factor=1)
        try:
            load_review_page(page, item['page'], report)
            if len(item['selector']) != 1:
                result['reason'] = 'unsupported_selector_chain'
            else:
                target = page.locator(item['selector'][0])
                if target.count() != 1:
                    result['reason'] = 'selector_not_unique'
                else:
                    # Open only ancestors the reviewer can reach through a
                    # native disclosure. Do not unhide arbitrary author content.
                    opened = target.evaluate("""e => {
                        let opened = 0;
                        for (let a = e.parentElement; a; a = a.parentElement) {
                            if (!a.matches('details:not([open])') ||
                                a.querySelector(':scope > summary')?.contains(e)) continue;
                            if (!a.querySelector(':scope > summary')) continue;
                            a.open = true; opened++;
                        }
                        e.scrollIntoView({block:'center', inline:'center', behavior:'instant'});
                        return opened;
                    }""")
                    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                    measured = page.evaluate(MEASURE_JS, [item])[0]
                    scroll_y = page.evaluate('scrollY')
                    for fragment in measured['fragments']:
                        for rect in fragment['rects']:
                            rect['top'] -= scroll_y
                            rect['bottom'] -= scroll_y
                    image = Image.open(BytesIO(page.screenshot(animations='disabled'))).convert('RGB')
                    result.update(score_item(measured, image))
                    result['opened_ancestor_disclosures'] = opened
        except Exception as exc:
            result['reason'] = f'capture_failed: {exc}'
        finally:
            page.close()
        results.append(result)
        print('REINSPECT', item['page'], width, item['selector'], result['status'], flush=True)
    return results


# Capture text-fragment foreground and geometry before hiding text. For sampling,
# hide only the *glyph fill* (not the computed `color` used by currentColor
# backgrounds/decoration), so gradients and pseudo-element paint remain visible.
MEASURE_JS = r'''(items) => {
  const output = [];
  const hide = new Set();
  const hiddenByDisclosure = el => {
    for (let details = el.parentElement; details; details = details.parentElement) {
      if (details.matches('details:not([open])') &&
          !details.querySelector(':scope > summary')?.contains(el)) return true;
    }
    return false;
  };
  for (const item of items) {
    let el;
    try { el = document.querySelector(item.selector[0]); }
    catch (_) { el = null; }
    if (!el) { output.push({...item, error: 'selector_not_found', fragments: []}); continue; }
    if (hiddenByDisclosure(el)) {
      output.push({...item, error: 'closed_disclosure', fragments: []}); continue;
    }
    if (el.closest('[aria-hidden="true"]') ||
        /Element content contains only non-text characters/i.test(item.failure_summary || '')) {
      output.push({...item, error: 'non_text', fragments: []}); continue;
    }
    hide.add(el);
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const fragments = [];
    let node;
    while ((node = walker.nextNode()) && fragments.length < 5) {
      if (!node.textContent.trim()) continue;
      const parent = node.parentElement;
      if (!parent || parent.closest('[aria-hidden="true"]') || hiddenByDisclosure(parent)) continue;
      const style = getComputedStyle(parent);
      if (style.display === 'none' || style.visibility !== 'visible') continue;
      const range = document.createRange(); range.selectNodeContents(node);
      const rects = [];
      for (const rect of range.getClientRects()) {
        if (rect.width <= 1 || rect.height <= 1) continue;
        let left = Math.max(0, rect.left), top = rect.top;
        let right = Math.min(window.innerWidth, rect.right), bottom = rect.bottom;
        for (let a = parent; a && a !== document.body; a = a.parentElement) {
          const s = getComputedStyle(a), b = a.getBoundingClientRect();
          if (/auto|hidden|scroll|clip/.test(s.overflowX)) {
            left = Math.max(left, b.left); right = Math.min(right, b.right);
          }
          if (/auto|hidden|scroll|clip/.test(s.overflowY)) {
            top = Math.max(top, b.top); bottom = Math.min(bottom, b.bottom);
          }
        }
        if (right - left < 3 || bottom - top < 3) continue;
        rects.push({left, right, top: top + scrollY, bottom: bottom + scrollY});
        if (rects.length >= 4) break;
      }
      if (!rects.length) continue;
      fragments.push({text: node.textContent.trim().slice(0, 80),
        color: style.color, fontSize: parseFloat(style.fontSize),
        weight: parseInt(style.fontWeight, 10) || 400, rects});
    }
    // Placeholder text is painted by the user agent, not a DOM text node.
    // Only compute a contrast pair for a *displayed* placeholder, never for a
    // populated input that merely retains a placeholder attribute. An opaque
    // solid control background is required later by score_solid_placeholder.
    let placeholder = null;
    if (!fragments.length && /^(INPUT|TEXTAREA)$/.test(el.tagName) &&
        el.placeholder && el.matches(':placeholder-shown') &&
        el.getClientRects().length) {
      const pseudo = getComputedStyle(el, '::placeholder');
      const style = getComputedStyle(el);
      if (style.display !== 'none' && style.visibility === 'visible') {
        placeholder = {
          text: el.placeholder.slice(0, 80),
          foreground: pseudo.color,
          background: style.backgroundColor,
          background_image: style.backgroundImage,
          opacity: pseudo.opacity,
          element_opacity: style.opacity,
          font_size_px: parseFloat(pseudo.fontSize),
          font_weight: parseInt(pseudo.fontWeight, 10) || 400
        };
      }
    }
    output.push({...item, fragments, placeholder,
      error: fragments.length ? null : 'no_visible_text_rect'});
  }
  for (const el of hide) {
    for (const node of [el, ...el.querySelectorAll('*')]) {
      node.style.setProperty('-webkit-text-fill-color', 'transparent', 'important');
      node.style.setProperty('text-shadow', 'none', 'important');
    }
  }
  return output;
}'''


def sample_rect_pixels(img, rect):
    """Interior positions provide a sampling heuristic, not every glyph pixel."""
    l, r, t, b = (rect[key] for key in ('left', 'right', 'top', 'bottom'))
    candidates = []
    for fx in (0.12, 0.30, 0.5, 0.7, 0.88):
        for fy in (0.20, 0.5, 0.80):
            x, y = round(l + (r-l)*fx), round(t + (b-t)*fy)
            if 0 <= x < img.width and 0 <= y < img.height:
                candidates.append(img.getpixel((x, y))[:3])
    return candidates



def score_solid_placeholder(item):
    """Compute visible placeholder contrast over a solid opaque control fill.

    This is *not* a pixel sample or a WCAG/paint certification. Background
    images, transparency, and potentially composited surfaces stay unresolved.
    """
    value = item.get('placeholder')
    if not value or not value.get('text') or value.get('background_image') != 'none':
        return None
    try:
        if (float(value.get('opacity', 0)) < 0.99999 or
                float(value.get('element_opacity', 0)) < 0.99999):
            return None
    except (ValueError, TypeError):
        return None
    foreground = parse_rgb(value.get('foreground', ''))
    background = parse_rgb(value.get('background', ''))
    if foreground is None or background is None:
        return None
    ratio = contrast_ratio(foreground, background)
    threshold = text_contrast_threshold(
        value.get('font_size_px', 16), value.get('font_weight', 400))
    return {
        'status': ('computed_placeholder_below_threshold'
                   if ratio < threshold else 'computed_placeholder_above_threshold'),
        'computed_ratio': round(ratio, 3),
        'threshold': threshold,
        'placeholder_text': value['text'],
        'foreground': value['foreground'],
        'background': value['background'],
        'method': 'computed visible placeholder foreground versus opaque solid control background',
    }

def score_item(item, img):
    result = {key: item[key] for key in ('page', 'selector', 'failure_summary')}
    result['status'] = 'unsampled'
    result['viewport_width'] = item['viewport_width']
    if item.get('error') == 'non_text':
        result['status'] = 'non_text'
        return result
    if item.get('error'):
        if item['error'] == 'no_visible_text_rect':
            placeholder = score_solid_placeholder(item)
            if placeholder is not None:
                result.update(placeholder)
                return result
        result['reason'] = item['error']
        return result
    scored = []
    for fragment in item['fragments']:
        fg = parse_rgb(fragment['color'])
        if fg is None:
            continue
        threshold = text_contrast_threshold(fragment['fontSize'], fragment['weight'])
        pixels = [pixel for rect in fragment['rects'] for pixel in sample_rect_pixels(img, rect)]
        if pixels:
            ratios = [contrast_ratio(fg, pixel) for pixel in pixels]
            scored.append({'foreground': fragment['color'], 'font_size_px': fragment['fontSize'],
                           'font_weight': fragment['weight'], 'text': fragment['text'],
                           'threshold': threshold, 'sampled_pixels': len(pixels),
                           'minimum_sampled_ratio': round(min(ratios), 3),
                           'median_sampled_ratio': round(sorted(ratios)[len(ratios)//2], 3)})
    if not scored:
        result['reason'] = 'no_resolvable_opaque_foreground_or_visible_sample_pixels'
        return result
    least = min(scored, key=lambda x: x['minimum_sampled_ratio'] - x['threshold'])
    result['minimum_sampled_ratio'] = least['minimum_sampled_ratio']
    result['threshold'] = least['threshold']
    result['worst_fragment'] = least
    result['fragments_sampled'] = len(scored)
    if any(frag['minimum_sampled_ratio'] < frag['threshold'] for frag in scored):
        result['status'] = 'sampled_below_threshold'
    elif any(frag['minimum_sampled_ratio'] < frag['threshold'] + 0.5 for frag in scored):
        result['status'] = 'narrow_margin'
    else:
        result['status'] = 'sampled_above_threshold'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--axe-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--widths', nargs='+', type=int, default=[1280, 390, 320])
    parser.add_argument('--pages', nargs='*', help='Optional exact page paths to sample')
    parser.add_argument('--reinspect-report', type=Path,
                        help='Revisit flagged observations from a previous triage report on the same content')
    args = parser.parse_args()
    from PIL import Image
    from playwright.sync_api import sync_playwright
    report = json.loads(args.axe_report.read_text(encoding='utf-8'))
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    clean = not subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
    observations = []
    with sync_playwright() as p:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        browser = p.chromium.launch(headless=True, **(
            {"executable_path": executable} if executable else {}))
        try:
            if args.reinspect_report:
                prior = json.loads(args.reinspect_report.read_text(encoding='utf-8'))
                observations = reinspect(browser, report, prior, args.widths, args.pages)
            for row in (() if args.reinspect_report else report['pages']):
                if args.pages and row['page'] not in args.pages:
                    continue
                items = [dict(item, page=row['page']) for item in row['incomplete']
                         if item['rule'] == 'color-contrast']
                if not items:
                    continue
                for width in args.widths:
                    page = browser.new_page(viewport={'width': width, 'height': 900}, device_scale_factor=1)
                    try:
                        load_review_page(page, row['page'], report)
                        measured = page.evaluate(MEASURE_JS, items)
                        for item in measured:
                            item['viewport_width'] = width
                        png = page.screenshot(full_page=True, animations='disabled')
                        image = Image.open(BytesIO(png)).convert('RGB')
                        observations.extend(score_item(item, image) for item in measured)
                        counts = status_counts(observations[-len(measured):])
                        print(row['page'], width, counts, flush=True)
                    except Exception as exc:
                        print('ERROR', row['page'], width, str(exc)[:150], flush=True)
                        observations.extend({'page': row['page'], 'viewport_width': width,
                            'selector': item['selector'], 'failure_summary': item['failure_summary'],
                            'status': 'unsampled', 'reason': f'capture_failed: {exc}'} for item in items)
                    finally:
                        page.close()
        finally:
            browser.close()
    review = {
        'method': 'Chromium pixel sampling plus computed opaque visible-placeholder colors; not WCAG certification',
        'capture_mode': 'viewport_reinspection' if args.reinspect_report else 'full_page_initial',
        'source_commit': head,
        'source_worktree_clean': clean,
        'source_axe_report': str(args.axe_report),
        'viewport_widths': args.widths,
        'limitations': ['Computed placeholder pairs do not certify painted glyphs, overlays or ancestor effects',
                        'Sampling does not certify glyph-level contrast or compositing accuracy',
                        'Pseudo-elements, occlusion, partial visibility and text shadows may affect samples',
                        'Interactive states, native OS contrast, real browser zoom, screen readers not tested',
                        'Manual adjudication of all axe incomplete nodes remains required'],
        'summary': status_counts(observations),
        'observations': observations,
    }
    if args.reinspect_report:
        review['source_triage_report'] = str(args.reinspect_report)
    args.output.write_text(json.dumps(review, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('TOTAL',review['summary'],'saved',args.output)
    for row in sorted((o for o in observations if o.get('minimum_sampled_ratio') is not None),
                      key=lambda o: o['minimum_sampled_ratio']-o['threshold'])[:20]:
        print('REVIEW', row['page'],row['viewport_width'],row['selector'],
              row['minimum_sampled_ratio'], 'needed',row['threshold'],row['status'])


if __name__ == '__main__':
    main()
