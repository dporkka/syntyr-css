/* Optional visual editor starters. The pages they produce are plain HTML/CSS.
   Sections come from the canonical vetted Blocks library, not runtime HTML. */
import {createBlock, createDefaultDocument, parseDocument} from "./page-builder-model.mjs";

export const STARTER_PAGES = Object.freeze([
  {
    id: "portfolio", label: "Creative portfolio",
    description: "Example portfolio starter with projects, a photo gallery, process and contact.",
    theme: "minimal", title: "Creative portfolio | Example",
    meta: "Example creative portfolio with selected projects and process.",
    hero: {
      eyebrow: "SELECTED WORK / EXAMPLE",
      title: "A place for work that speaks clearly.",
      description: "Introduce your projects, process and perspective. Replace all sample text and imagery before publishing.",
      actionText: "View projects", actionHref: "#block-starter-1"
    },
    sections: ["section:image-gallery", "section:image-story", "section:process-steps", "cta", "footer"],
    overrides: { cta: {heading: "Have a project in mind?", actionText: "Get in touch", actionHref: "/contact"},
      footer: {brand: "Your creative studio"} }
  },
  {
    id: "agency", label: "Agency website",
    description: "Example agency starter with service offerings, projects, process and inquiry.",
    theme: "studio", title: "Creative agency | Example",
    meta: "Example independent agency services, case studies and contact page.",
    hero: {
      eyebrow: "INDEPENDENT STUDIO / EXAMPLE",
      title: "We bring ideas into focus.",
      description: "Show what you offer, how you collaborate, and the next step for prospective clients.",
      actionText: "Our services", actionHref: "#block-starter-1"
    },
    sections: ["section:services-grid", "section:portfolio-grid", "section:process-steps",
      "section:contact-quote", "footer"],
    overrides: {footer: {brand:"Your agency"}}
  },
  {
    id: "saas", label: "SaaS landing page",
    description: "Example SaaS starter with benefits, pricing, FAQ and a product CTA.",
    theme: "corporate", title: "SaaS landing page | Example",
    meta: "Example SaaS product marketing page with benefits and pricing placeholders.",
    hero: {
      eyebrow: "YOUR PRODUCT / EXAMPLE",
      title: "Show the value of your software.",
      description: "A focused introduction to your product's workflow and benefits. Replace sample features and plans before publishing.",
      actionText: "Explore features", actionHref: "#block-starter-1"
    },
    sections: ["section:feature-grid", "section:pricing-trio", "faq", "cta", "footer"],
    overrides: {
      faq: {heading: "Product questions", firstQuestion: "How do I get started?",
        firstAnswer: "Replace this example with your onboarding and signup instructions.",
        secondQuestion: "What is included in each plan?",
        secondAnswer: "Document your actual features, plan limits and billing terms here."},
      cta: {heading: "Ready to explore?", actionText: "Request a demo", actionHref:"/demo"},
      footer: {brand:"Your SaaS product"}
    }
  },
  {
    id: "small-business", label: "Local business",
    description: "Example small-business starter with services, coverage, opening hours and contact.",
    theme: "minimal", title: "Local business | Example",
    meta: "Example local business services and locations with placeholder opening hours.",
    hero: {
      eyebrow: "LOCAL SERVICES / EXAMPLE",
      title: "Make it easy for customers to find you.",
      description: "Explain your services, operating area, contact details and hours in one accessible page.",
      actionText: "See services", actionHref: "#block-starter-1"
    },
    sections: ["section:services-grid", "section:service-areas", "section:locations-hours",
      "section:contact-quote", "footer"],
    overrides: {footer: {brand:"Your local business"}}
  }
]);

export function createStarterPage(id) {
  const starter = STARTER_PAGES.find(entry => entry.id === id);
  if (!starter) throw new Error("Unknown starter page: " + id);
  const page = createDefaultDocument();
  page.title = starter.title;
  page.description = starter.meta;
  page.theme = starter.theme;
  page.blocks = [
    {...createBlock("hero", "hero-1"), props:{...createBlock("hero").props,...starter.hero}},
    ...starter.sections.map((type, index) => {
      const block = createBlock(type, "starter-" + (index + 1));
      if (starter.overrides?.[type])
        block.props = {...block.props, ...starter.overrides[type]};
      return block;
    })
  ];
  // Keep starter data in the same validated, editable document contract.
  return parseDocument(page);
}
