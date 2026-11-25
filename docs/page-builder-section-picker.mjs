/* Docs-only use-case suggestions and cheap layout sketches. No consumer runtime. */
export const SECTION_USE_CASES = Object.freeze([
  {id: "all", label: "All sections", description: "Browse every copy-owned layout."},
  {id: "landing", label: "Landing pages", description: "Hero, features, proof, pricing, navigation and conversion."},
  {id: "saas", label: "SaaS & dashboards", description: "Operational screens, technical docs and product onboarding."},
  {id: "business", label: "Agencies & companies", description: "Service explanations, people, company information and contact."},
  {id: "publishing", label: "Blogs & documentation", description: "Editorial reading, articles, guides, resources and navigation."},
  {id: "commerce", label: "Shops & products", description: "Collections, product details, pricing and support links."},
  {id: "portfolio", label: "Portfolios & galleries", description: "Work, case studies, original imagery and storytelling."},
  {id: "navigation", label: "Headers & footers", description: "Site navigation and reusable layout edges."}
]);

const USE_CASE_RULES = Object.freeze({
  landing: {
    categories: ["Marketing"],
    ids: ["site-header", "header-centered", "header-split", "footer-compact", "footer-sitemap",
      "site-footer", "contact-quote", "company-story", "services-grid", "decision-guide"]
  },
  saas: {
    categories: ["Applications", "Technical"],
    ids: ["site-header", "header-split", "site-footer", "footer-sitemap", "pricing-trio",
      "pricing-comparison", "feature-rows", "impact-narrative"]
  },
  business: {
    categories: ["Services", "Company"],
    ids: ["site-header", "header-centered", "footer-sitemap", "site-footer",
      "editorial-intro-split", "customer-reviews", "impact-narrative"]
  },
  publishing: {
    categories: ["Editorial", "Publishing"],
    ids: ["docs-layout", "header-centered", "header-disclosure", "site-footer",
      "footer-newsletter", "resource-index", "faq-sidecar"]
  },
  commerce: {
    categories: ["Commerce"],
    ids: ["site-header", "header-split", "site-footer", "footer-sitemap", "pricing-trio",
      "pricing-comparison", "customer-reviews", "faq", "faq-sidecar"]
  },
  portfolio: {
    categories: ["Portfolio"],
    ids: ["header-centered", "site-footer", "footer-compact", "image-story", "hero-photo",
      "editorial-intro-split", "company-story", "testimonials-grid"]
  },
  navigation: {categories: ["Navigation"], ids: []}
});

export function sectionMatchesUseCase(type, definition, useCase = "all") {
  if (useCase === "all") return true;
  const rule = USE_CASE_RULES[useCase];
  if (!rule || !definition || !type.startsWith("section:")) return false;
  return rule.categories.includes(definition.category) ||
    rule.ids.includes(type.slice("section:".length));
}

export function filterSections(types, resolve, {query = "", category = "all", useCase = "all"} = {}) {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return types.filter(type => {
    const def = resolve(type);
    if (!def || (category !== "all" && def.category !== category)) return false;
    if (!sectionMatchesUseCase(type, def, useCase)) return false;
    const searchable = (def.label + " " + def.description + " " + def.category + " " + type)
      .toLocaleLowerCase();
    return terms.every(term => searchable.includes(term));
  });
}

export function sectionThumbnailPattern(type) {
  const name = type.replace(/^section:/, "");
  if (/(header|footer|navigation|social-links|logo-wall)/.test(name)) return "navigation";
  if (/(image|gallery|photo|portfolio|before-after|product-preview)/.test(name)) return "media";
  if (/(metric|stat|impact|billing-usage|telemetry)/.test(name)) return "stats";
  if (/(article|docs|resource-index|content-collection|press-highlights|release-notes)/.test(name)) return "article";
  if (/(faq-sidecar|split|sidecar|spotlight|story)/.test(name)) return "split";
  if (/(form|auth-|contact-quote|newsletter|registration|settings)/.test(name)) return "form";
  if (/(row|steps|timeline|process)/.test(name)) return "rows";
  if (/(grid|cards|pricing|comparison|directory|collection|features|services|team|principles|decision|bento|sitemap)/.test(name)) return "grid";
  return "standard";
}
