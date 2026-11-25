"""Optional rendered application typography checks across theme, density and viewport."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
ROOT = Path(__file__).resolve().parents[1]
THEMES = ('studio','grid','noir','industrial','terminal','corporate','minimal')

def verify(browser):
    page = browser.new_page()
    css = (ROOT / 'dist/syntyr.core.css').read_text()
    for width in (320, 390, 768, 1024, 1440, 1920):
        page.set_viewport_size({'width':width,'height':900})
        for theme in THEMES:
            page.set_content(f'<section class="syn-root" data-syn-theme="{theme}" data-syn-typography="application"><h1 class="syn-page-title">Application overview</h1><h2 class="syn-section-heading">Customer accounts</h2><h3 class="syn-card-heading">Recent activity</h3><p class="syn-body">Supporting content</p><h2 class="syn-display">Display</h2><code class="syn-code">id-123</code></section><h1 class="syn-page-title" id="host">Host</h1>')
            page.add_style_tag(content=css)
            result=page.evaluate("""() => {
                const root=document.querySelector('.syn-root');
                const style=s=>getComputedStyle(root.querySelector(s));
                const fonts=getComputedStyle(root);
                const before=style('.syn-page-title').fontSize;
                root.dataset.synDensity='compact';
                return {page:parseFloat(before),card:parseFloat(style('.syn-card-heading').fontSize),section:parseFloat(style('.syn-section-heading').fontSize),
                  densityStable:before===style('.syn-page-title').fontSize,
                  ui:style('.syn-page-title').fontFamily,body:style('.syn-body').fontFamily,
                  display:style('.syn-display').fontFamily,code:style('.syn-code').fontFamily,
                  mono:fonts.getPropertyValue('--syn-mono').trim(),
                  base:fonts.getPropertyValue('--syn-font').trim(),
                  overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
                  host:getComputedStyle(document.getElementById('host')).fontFamily};
            }""")
            assert result['page']>result['section']>result['card'],(theme,width,result)
            assert result['densityStable'] and not result['overflow'],(theme,width,result)
            assert result['ui']==result['body'] and 'system-ui' in result['ui'],(theme,width,result)
            if theme in ('grid','terminal'):
                assert 'monospace' in result['display'] and 'monospace' in result['code'],result
            assert result['host']!=result['ui'],result
    # Legacy Grid stays technical; nested opt-in scopes and theme resets
    # must not change sibling regions or overwrite unrelated palette aliases.
    page.set_content("""<main class="syn-root" data-syn-theme="grid">
      <p id="legacy" class="syn-body">Legacy</p>
      <section data-syn-typography="application">
        <p id="profile" class="syn-body">Profile</p>
        <section data-syn-theme="terminal"><p id="reset" class="syn-body">Reset</p></section>
        <section data-syn-theme="terminal" data-syn-typography="application"><p id="both" class="syn-body">Both</p></section>
      </section><p id="sibling" class="syn-body">Sibling</p>
    </main>""")
    page.add_style_tag(content=css)
    fonts=page.evaluate("""() => Object.fromEntries(['legacy','profile','reset','both','sibling'].map(id=>[id,getComputedStyle(document.getElementById(id)).fontFamily]))""")
    assert 'monospace' in fonts['legacy'] and fonts['legacy']==fonts['sibling']==fonts['reset'],fonts
    assert 'system-ui' in fonts['profile'] and fonts['profile']==fonts['both'],fonts
    page.close()

if __name__=='__main__':
    with sync_playwright() as p:
        engine=sys.argv[1] if len(sys.argv)>1 else 'chromium'
        browser=getattr(p,engine).launch(headless=True)
        try:
            verify(browser)
            print(f'PASS {engine}: 42 theme/viewport cases',flush=True)
        finally:
            browser.close()
