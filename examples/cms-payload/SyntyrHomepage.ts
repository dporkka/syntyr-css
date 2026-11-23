/**
 * Optional Payload 3 GlobalConfig for the Syntyr CMS v1 page content.
 * Copy into an existing authenticated Payload application. Do not add Payload
 * to @syntyr/css. Access checks must be supplied explicitly by the host.
 *
 * Payload uses blockType and its own array-row IDs. The build-time exporter
 * removes only known persistence metadata and converts fields to portable
 * { type, id, ... } sections, with strict validation before publishing.
 */
import type { Block, Field, GlobalConfig } from 'payload';

const text = (name: string, label: string, maxLength = 1000): Field => ({
  name,
  label,
  type: 'text',
  required: true,
  minLength: 1,
  maxLength,
});

const buttonField = (): Field => ({
  name: 'button',
  label: 'Button',
  type: 'group',
  fields: [text('label', 'Button label', 100), text('url', 'Button URL', 2048)],
});

const sectionId: Field = {
  name: 'sectionId',
  label: 'Stable section ID (lowercase slug)',
  type: 'text',
  required: true,
  minLength: 1,
  maxLength: 63,
};

const heading = () => text('heading', 'Heading', 180);
const featureFields: Field[] = [
  text('title', 'Feature title', 1000),
  text('description', 'Feature description', 1000),
];

const hero: Block = {
  slug: 'hero',
  fields: [
    sectionId,
    text('eyebrow', 'Eyebrow', 120),
    heading(),
    text('description', 'Description', 500),
    buttonField(),
  ],
};

const features: Block = {
  slug: 'features',
  fields: [
    sectionId,
    heading(),
    { name: 'items', type: 'array', label: 'Feature cards',
      required: true, minRows: 1, maxRows: 24, fields: featureFields },
  ],
};

const pricing: Block = {
  slug: 'pricing',
  fields: [
    sectionId,
    heading(),
    { name: 'plans', type: 'array', label: 'Plans',
      required: true, minRows: 1, maxRows: 6, fields: [
        text('name', 'Plan name', 100),
        text('price', 'Displayed price', 100),
        { name: 'features', type: 'array', label: 'Benefits',
          required: true, minRows: 1, maxRows: 24,
          fields: [text('feature', 'Benefit', 200)] },
        buttonField(),
      ] },
  ],
};

const faq: Block = {
  slug: 'faq',
  fields: [
    sectionId,
    heading(),
    { name: 'items', type: 'array', label: 'Questions',
      required: true, minRows: 1, maxRows: 24, fields: [
        text('question', 'Question', 1000),
        text('answer', 'Answer', 1000),
      ] },
  ],
};

const cta: Block = {
  slug: 'cta',
  fields: [
    sectionId,
    heading(),
    text('description', 'Description', 500),
    buttonField(),
  ],
};

/** Blocks can be reused in site-specific collections or globals. */
export const syntyrPageSections: Field = {
  name: 'sections',
  label: 'Syntyr page sections',
  type: 'blocks',
  required: true,
  minRows: 1,
  maxRows: 24,
  blocks: [hero, features, pricing, faq, cta],
};

/**
 * Do not silently expose the CMS Global through default access rules.
 * Host applications must pass explicit, authenticated read/update policies.
 *
 * This prevents an example config from accidentally publishing drafts or
 * allowing unauthenticated content edits.
 */
export function createSyntyrHomepageGlobal(
  access: NonNullable<GlobalConfig['access']>,
): GlobalConfig {
  if (!access?.read || !access?.update) {
    throw new Error('Provide explicit read and update access policies for Syntyr CMS');
  }
  return {
    slug: 'syntyrHome',
    label: 'Syntyr homepage',
    access: access,
    fields: [
      text('title', 'SEO title', 180),
      text('description', 'Meta description', 500),
      { name: 'theme', type: 'select', label: 'Syntyr theme', required: true,
        defaultValue: 'studio',
        options: ['studio', 'grid', 'noir', 'industrial', 'terminal', 'corporate', 'minimal'] },
      syntyrPageSections,
    ],
  };
}
