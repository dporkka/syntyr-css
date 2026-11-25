# Syntyr blog (static site)

The blog is authored in semantic HTML and styled with the same MIT Syntyr CSS
components and optional recipes used throughout the public site. It has **no
runtime JavaScript**, remote fonts, CMS, or markdown parser.

## Add an article

1. Copy an existing `blog/<slug>.html` article to `blog/<new-slug>.html`.
2. Replace its visible text, `<title>`, description, Open Graph title,
   canonical URL and `BlogPosting` JSON-LD (`headline`, publication date,
   description, canonical mainEntityOfPage). Keep a single h1.
3. Add an article card linking to it in `blog/index.html` and an RSS item in
   `blog/rss.xml`, using a valid RFC 822 `pubDate`. Keep newest items first.
4. Explicitly allowlist its file in `scripts/build_cloudflare_site.py`.
   Only reviewed public assets are published; this README is private.
5. Update the `POSTS` constant in `tests/test_blog_site.py`. Add semantic
   headings, Syntyr components and links to genuine docs or examples.

The Cloudflare build generates canonical metadata and the sitemap from the
allowlisted HTML files. The checked-in links use `.html` for local preview;
Cloudflare Pages redirects them to clean canonical URLs in production.
Syntyr stylesheets are content-hashed by the production site build.

## Verify

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -p test_blog_site.py -v
python3 -m unittest discover -s tests -p test_cloudflare_site.py -v
python3 -m unittest discover -s tests -p test_seo_site.py -v
python3 scripts/build_cloudflare_site.py
python3 scripts/build_cloudflare_site.py --check
```

Blog-specific layout tweaks stay in `blog/blog.css`. Reuse `syn-*`
classes from core/recipes, and avoid adding new global component APIs for
content pages.
