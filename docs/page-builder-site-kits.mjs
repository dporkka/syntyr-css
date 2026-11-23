/* Optional multi-page starter kits. Authored here, never loaded by exported sites.
   Built exclusively from validated native blocks and the copy-owned section catalog. */
import {createBlock, createDefaultDocument, parseDocument} from "./page-builder-model.mjs";
import {createStarterPage} from "./page-builder-starters.mjs";
import {createSiteProject, parseSiteProject} from "./site-builder-model.mjs";

const SPECS = [
  {
    id: "portfolio", label: "Portfolio website kit", brand: "Your creative studio",
    description: "Example portfolio site with projects and contact pages. No client claims or configured inbox.",
    nav: {label: "Get in touch", slug: "contact"},
    pages: [
      {slug: "projects", title: "Projects | Example portfolio",
        meta: "Example project gallery. Replace every project and photograph before publishing.",
        eyebrow: "EXAMPLE WORK", heading: "Selected projects and experiments.",
        summary: "Show work you have permission to publish, including project context and outcomes.",
        sections: ["section:image-gallery", "section:portfolio-grid"]},
      {slug: "contact", title: "Contact | Example portfolio",
        meta: "Example portfolio contact layout; connect your own form endpoint.",
        eyebrow: "START A CONVERSATION", heading: "Tell us about your project.",
        summary: "Explain how clients can reach your studio. Connect the form to your own server.",
        sections: ["section:contact-quote"]}
    ]
  },
  {
    id: "agency", label: "Agency website kit", brand: "Your agency",
    description: "Example agency website with services and inquiry pages. Customize content and connect forms.",
    nav: {label: "Contact us", slug: "contact"},
    pages: [
      {slug: "services", title: "Services | Example agency",
        meta: "Illustrative agency services and process; replace sample descriptions.",
        eyebrow: "WHAT WE DO", heading: "Explain your services clearly.",
        summary: "Describe the scope, process and deliverables of services you actually provide.",
        sections: ["section:services-grid", "section:process-steps"]},
      {slug: "contact", title: "Contact | Example agency",
        meta: "Illustrative agency inquiry page; connect the form to your server.",
        eyebrow: "PROJECT INQUIRIES", heading: "Start with a brief conversation.",
        summary: "Set expectations for inquiries and tell visitors how to contact your team.",
        sections: ["section:contact-quote"]}
    ]
  },
  {
    id: "saas", label: "SaaS website kit", brand: "Your SaaS product",
    description: "Example SaaS site with features, pricing and contact pages. Plans are placeholders.",
    nav: {label: "View pricing", slug: "pricing"},
    pages: [
      {slug: "features", title: "Features | Example SaaS",
        meta: "Example product feature page; verify every feature claim.",
        eyebrow: "PRODUCT FEATURES", heading: "Show the product workflow.",
        summary: "Use accurate screenshots and descriptions of functionality that exists.",
        sections: ["section:feature-grid", "section:process-steps"]},
      {slug: "pricing", title: "Pricing | Example SaaS",
        meta: "Illustrative software pricing; replace plans and billing terms.",
        eyebrow: "EXAMPLE PLANS", heading: "Make your pricing easy to understand.",
        summary: "These plans and prices are illustrative. Replace them before launch.",
        sections: ["section:pricing-trio", "faq"]},
      {slug: "contact", title: "Contact | Example SaaS",
        meta: "Example SaaS sales inquiry page; connect forms to your own application.",
        eyebrow: "PRODUCT INQUIRIES", heading: "Ask about the product.",
        summary: "Provide your actual sales, support and onboarding contact details.",
        sections: ["section:contact-quote"]}
    ]
  },
  {
    id: "small-business", label: "Local business website kit", brand: "Your local business",
    description: "Example local-business website with services, locations and contact. Replace all operating details.",
    nav: {label: "Contact us", slug: "contact"},
    pages: [
      {slug: "services", title: "Services | Example local business",
        meta: "Illustrative local services; replace examples with your actual offerings.",
        eyebrow: "LOCAL SERVICES", heading: "Make your services easy to find.",
        summary: "Explain service areas and how customers can request an estimate.",
        sections: ["section:services-grid", "section:service-areas"]},
      {slug: "locations", title: "Locations | Example local business",
        meta: "Illustrative opening hours and locations, not verified business information.",
        eyebrow: "VISIT OR CALL", heading: "Show accurate hours and locations.",
        summary: "Replace every sample address, opening hour and contact detail.",
        sections: ["section:locations-hours"]},
      {slug: "contact", title: "Contact | Example local business",
        meta: "Example local-business inquiry page; a backend is required to receive submissions.",
        eyebrow: "GET IN TOUCH", heading: "Request information.",
        summary: "Provide your verified contact details and configure your own form handler.",
        sections: ["section:contact-quote"]}
    ]
  }
];

export const STARTER_SITE_KITS = Object.freeze(SPECS.map(spec => Object.freeze({
  id: spec.id, label: spec.label, description: spec.description, pages: spec.pages.length + 1
})));

function makeInnerPage(spec, pageSpec) {
  const page = createDefaultDocument();
  page.title = pageSpec.title;
  page.description = pageSpec.meta;
  page.theme = createStarterPage(spec.id).theme;
  const hero = createBlock("hero", "hero-1");
  hero.props = {
    eyebrow: pageSpec.eyebrow, title: pageSpec.heading,
    description: pageSpec.summary, actionText: "Explore below",
    actionHref: "#block-kit-1"
  };
  page.blocks = [hero, ...pageSpec.sections.map((type, index) =>
    createBlock(type, "kit-" + (index + 1)))];
  return parseDocument(page);
}

export function createStarterSite(id) {
  const spec = SPECS.find(item => item.id === id);
  if (!spec) throw new Error("Unknown site kit: " + id);
  const home = createStarterPage(id);
  // Shared site footer replaces the standalone starter footer; do not render twice.
  home.blocks = home.blocks.filter(block => block.type !== "footer");
  for (const block of home.blocks)
    if (block.type === "cta" && block.props.actionHref === "/demo")
      block.props.actionHref = "/contact/";
  const site = createSiteProject(parseDocument(home));
  for (const entry of spec.pages)
    site.pages.push({slug: entry.slug, document: makeInnerPage(spec, entry)});
  const header = createBlock("header", "site-header");
  header.props = {brand: spec.brand, linkText: spec.nav.label, linkHref: "/" + spec.nav.slug + "/"};
  const footer = createBlock("footer", "site-footer");
  footer.props = {brand: spec.brand,
    description: "Example site. Replace content and configure form destinations before publishing.",
    linkText: "Home", linkHref: "/"};
  site.shared = {header, footer};
  return parseSiteProject(site);
}
