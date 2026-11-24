import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  SECTION_USE_CASES, sectionMatchesUseCase, filterSections, sectionThumbnailPattern
} from '../docs/page-builder-section-picker.mjs';

const sections = JSON.parse(readFileSync(new URL('../metadata/section-composer.v1.json', import.meta.url), 'utf8')).sections;
const types = sections.map(section => 'section:' + section.id);
const byType = new Map(sections.map(section => ['section:' + section.id, {
  label: section.title, description: section.description, category: section.category
}]));
const resolve = type => byType.get(type);

test('use-case groups are unique, understandable and cover every source section', () => {
  const names = SECTION_USE_CASES.map(({id}) => id);
  assert.deepEqual(names.slice(0, 1), ['all']);
  assert.equal(new Set(names).size, names.length);
  assert.ok(SECTION_USE_CASES.length >= 6);
  for (const item of SECTION_USE_CASES) {
    assert.ok(item.label.length >= 4 && item.description.length >= 12, item.id);
  }
  for (const type of types) {
    assert.ok(SECTION_USE_CASES.slice(1).some(({id}) => sectionMatchesUseCase(type, resolve(type), id)), type);
  }
  assert.equal(filterSections(types, resolve).length, sections.length);
});

test('curated use cases cross category boundaries and preserve all-category search', () => {
  const landing = filterSections(types, resolve, {useCase: 'landing'});
  assert.ok(landing.includes('section:hero-product'));
  assert.ok(landing.includes('section:site-header'));
  assert.ok(landing.includes('section:contact-quote'));
  const docs = filterSections(types, resolve, {useCase: 'publishing'});
  assert.ok(docs.includes('section:article-toc'));
  assert.ok(docs.includes('section:resource-index'));
  assert.ok(docs.includes('section:docs-layout'));
  const commerce = filterSections(types, resolve, {useCase: 'commerce'});
  assert.ok(commerce.includes('section:product-collection'));
  assert.ok(commerce.includes('section:site-footer'));
  assert.ok(!commerce.includes('section:crm-workspace'));
  assert.deepEqual(filterSections(types, resolve, {query: 'sitemap', category: 'Navigation'}), ['section:footer-sitemap']);
  assert.deepEqual(filterSections(types, resolve, {query: 'image gallery', category: 'Portfolio'}),
    ['section:portfolio-grid', 'section:image-gallery']);
  assert.deepEqual(filterSections(types, resolve, {useCase: 'unknown'}), []);
});

test('lightweight thumbnails use deterministic patterns, not remote imagery', () => {
  const patterns = new Set(['split', 'grid', 'article', 'navigation', 'stats', 'form', 'media', 'rows', 'standard']);
  for (const type of types) assert.ok(patterns.has(sectionThumbnailPattern(type)), type);
  assert.equal(sectionThumbnailPattern('section:header-centered'), 'navigation');
  assert.equal(sectionThumbnailPattern('section:footer-sitemap'), 'navigation');
  assert.equal(sectionThumbnailPattern('section:article-toc'), 'article');
  assert.equal(sectionThumbnailPattern('section:impact-narrative'), 'stats');
  assert.equal(sectionThumbnailPattern('section:image-gallery'), 'media');
  assert.equal(sectionThumbnailPattern('section:faq-sidecar'), 'split');
});
