"""Explicit dimensional query inventory, with browser probes at adjacent CSS pixels."""


def adjacent_pixels(rem):
    px = round(rem * 16)
    return px - 1, px, px + 1


# (source, condition, threshold rem, published example)
MEDIA = (
    ("src/semantic.css", "(max-width: 40rem)", 40, "examples/semantic-starter.html"),
    ("src/recipes.css", "(max-width: 40rem)", 40, "examples/premium-compositions.html"),
    ("src/recipes.css", "(min-width: 53rem)", 53, "examples/saas.html"),
    ("src/recipes.css", "(max-width: 30rem)", 30, "examples/enterprise-compositions.html"),
    ("src/media.css", "(max-width: 48rem)", 48, "examples/media-entertainment.html"),
    ("src/components/overlays.css", "(max-height: 30rem)", 30, "examples/dropdowns.html"),
)

# (source, query, threshold rem, fixture id)
CONTAINERS = (
    ("src/recipes.css", "syn-resizable-workspace (max-width: 44rem)", 44, "workspace"),
    ("src/recipes.css", "syn-record-fields (max-width: 24rem)", 24, "record"),
    ("src/recipes.css", "(min-width: 37rem)", 37, "bento"),
    ("src/native-recipes.css", "syn-floating-field (max-width: 21rem)", 21, "floating"),
    ("src/geo.css", "syn-geo (max-width: 48rem)", 48, "geo"),
    ("src/geo.css", "syn-geo (max-width: 26rem)", 26, "geo"),
    ("src/email.css", "syn-email (min-width: 48rem)", 48, "email"),
    ("src/components/patterns.css", "syn-region (min-width: 31rem)", 31, "region"),
    ("src/components/patterns.css", "syn-region (min-width: 43rem)", 43, "region"),
    ("src/components/patterns.css", "syn-region (min-width: 55rem)", 55, "region"),
    ("src/components/form-composition.css", "syn-region (min-width: 42rem)", 42, "region"),
    ("src/components/form-composition.css", "(max-width: 12rem)", 12, "input"),
)
