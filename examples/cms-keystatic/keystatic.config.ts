/**
 * Optional Keystatic editor, NOT imported by Syntyr CSS.
 *
 * Copy this config into an Astro/Next project with Keystatic installed.
 * Keystatic stores typed fields.blocks as {discriminant, value}; run the
 * build-time export script to obtain the portable Syntyr JSON contract.
 * Local storage is deliberately the only enabled backend in this example.
 */
import { config, fields, singleton } from '@keystatic/core';

const required = (label: string, multiline = false) =>
  fields.text({ label, multiline, validation: { isRequired: true } });

const button = () => fields.object(
  {
    label: required('Button label'),
    url: required('Button URL (root-relative or HTTPS)'),
  },
  { label: 'Button' },
);

const sectionId = () => required('Stable section ID (lowercase slug)');

export default config({
  storage: { kind: 'local' },
  singletons: {
    homepage: singleton({
      label: 'Syntyr homepage',
      path: 'content/pages/home',
      format: { data: 'json' },
      schema: {
        title: required('SEO title'),
        description: required('Meta description', true),
        theme: fields.select({
          label: 'Syntyr theme',
          options: [
            { label: 'Studio', value: 'studio' },
            { label: 'Grid', value: 'grid' },
            { label: 'Noir', value: 'noir' },
            { label: 'Industrial', value: 'industrial' },
            { label: 'Terminal', value: 'terminal' },
            { label: 'Corporate', value: 'corporate' },
            { label: 'Minimal', value: 'minimal' },
          ],
          defaultValue: 'studio',
        }),
        sections: fields.blocks(
          {
            hero: {
              label: 'Hero',
              schema: fields.object({
                id: sectionId(),
                eyebrow: required('Eyebrow'),
                heading: required('Heading'),
                description: required('Description', true),
                button: button(),
              }),
            },
            features: {
              label: 'Features',
              schema: fields.object({
                id: sectionId(),
                heading: required('Heading'),
                items: fields.array(
                  fields.object({
                    title: required('Feature title'),
                    description: required('Feature description', true),
                  }),
                  { label: 'Feature cards', itemLabel: props => props.fields.title.value || 'Feature' },
                ),
              }),
            },
            pricing: {
              label: 'Pricing',
              schema: fields.object({
                id: sectionId(),
                heading: required('Heading'),
                plans: fields.array(
                  fields.object({
                    name: required('Plan name'),
                    price: required('Displayed price'),
                    features: fields.array(required('Benefit'), { label: 'Benefits' }),
                    button: button(),
                  }),
                  { label: 'Pricing plans', itemLabel: props => props.fields.name.value || 'Plan' },
                ),
              }),
            },
            faq: {
              label: 'FAQ',
              schema: fields.object({
                id: sectionId(),
                heading: required('Heading'),
                items: fields.array(
                  fields.object({
                    question: required('Question'),
                    answer: required('Answer', true),
                  }),
                  { label: 'Questions', itemLabel: props => props.fields.question.value || 'FAQ item' },
                ),
              }),
            },
            cta: {
              label: 'Call to action',
              schema: fields.object({
                id: sectionId(),
                heading: required('Heading'),
                description: required('Description', true),
                button: button(),
              }),
            },
          },
          { label: 'Page sections' },
        ),
      },
    }),
  },
});
