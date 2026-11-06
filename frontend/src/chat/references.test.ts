import { describe, expect, it } from 'vitest';
import type { Citation, WebSource } from '../api/types';
import { domainOf, findReference, linkReferences, referencesIn, unmatchedReferences, visibleText } from './references';

const D6: Citation = { id: 'D6', doc: 'atlas_context.md', section: 'Store closures', excerpt: 'Closed in March.', score: null };
const W1: WebSource = { id: 'W1', title: 'Retail news', url: 'https://www.example.org/news', published: '2026-10-12' };

describe('visibleText', () => {
  it('holds back an unclosed reference at the end while the answer streams', () => {
    expect(visibleText('closed for a renovation [', true)).toBe('closed for a renovation ');
    expect(visibleText('closed for a renovation [D', true)).toBe('closed for a renovation ');
    expect(visibleText('closed for a renovation [D12', true)).toBe('closed for a renovation ');
    expect(visibleText('see [W', true)).toBe('see ');
  });

  it('shows closed references, other brackets and a finished answer as they are', () => {
    expect(visibleText('renovation [D6]', true)).toBe('renovation [D6]');
    expect(visibleText('a list [like this', true)).toBe('a list [like this');
    expect(visibleText('renovation [D', false)).toBe('renovation [D');
  });

  it('rebuilds a reference split across two text events', () => {
    let text = 'The store was closed for a full renovation [D';
    expect(linkReferences(visibleText(text, true), [], [], false)).toBe('The store was closed for a full renovation ');
    text += '6].';
    expect(linkReferences(visibleText(text, true), [D6], [], false)).toBe(
      'The store was closed for a full renovation [D6](#ref-D6).',
    );
  });
});

describe('linkReferences', () => {
  it('turns matched references into chip links', () => {
    expect(linkReferences('Closed [D6], see [W1].', [D6], [W1], true)).toBe('Closed [D6](#ref-D6), see [W1](#ref-W1).');
  });

  it('keeps a chip waiting while its item has not arrived yet', () => {
    expect(linkReferences('Closed [D6].', [], [], false)).toBe('Closed [D6](#ref-D6).');
  });

  it('leaves a reference with no match as plain text once the answer has ended', () => {
    expect(linkReferences('Closed [D6] and [D9].', [D6], [], true)).toBe('Closed [D6](#ref-D6) and [D9].');
  });
});

describe('reference matching', () => {
  it('finds a D reference in the citations and a W reference in the sources', () => {
    expect(findReference('D6', [D6], [W1])).toEqual({ id: 'D6', kind: 'D', item: D6 });
    expect(findReference('W1', [D6], [W1])).toEqual({ id: 'W1', kind: 'W', item: W1 });
    expect(findReference('W6', [D6], [W1])).toBeNull();
    expect(findReference('D1', [D6], [W1])).toBeNull();
  });

  it('lists the references of a text, and the ones that match nothing', () => {
    const text = 'Closed [D6] [D6], news [W1] and [W2], notes [D9].';
    expect(referencesIn(text)).toEqual(['D6', 'W1', 'W2', 'D9']);
    expect(unmatchedReferences(text, [D6], [W1])).toEqual(['W2', 'D9']);
  });

  it('shows the domain of a source without www', () => {
    expect(domainOf('https://www.example.org/news')).toBe('example.org');
    expect(domainOf('not a url')).toBe('not a url');
  });
});
