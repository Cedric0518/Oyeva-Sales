import type { Citation, WebSource } from '../api/types';

/** `[D6]`: a section of the user's document. `[W1]`: a web source (docs/contract.md, section 7). */
export const REFERENCE = /\[(D|W)(\d+)\]/g;

/** An unclosed reference at the end of a text still streaming: `[`, `[D`, `[D1`... */
const UNCLOSED = /\[(?:[DW]\d{0,3})?$/;

/**
 * The text to show while it streams. A reference can be split across two `text` events
 * (`[D` then `6]`): an unclosed `[` of up to 6 characters at the end waits for the next event.
 */
export function visibleText(text: string, streaming: boolean): string {
  if (!streaming) return text;
  const match = UNCLOSED.exec(text);
  return match && text.length - match.index <= 6 ? text.slice(0, match.index) : text;
}

export type Reference = { id: string; kind: 'D'; item: Citation } | { id: string; kind: 'W'; item: WebSource };

/** The citation or the web source a reference points to, or null if it has not arrived (yet). */
export function findReference(id: string, citations: Citation[], sources: WebSource[]): Reference | null {
  if (id.startsWith('D')) {
    const item = citations.find((c) => c.id === id);
    return item ? { id, kind: 'D', item } : null;
  }
  const item = sources.find((s) => s.id === id);
  return item ? { id, kind: 'W', item } : null;
}

/**
 * Markdown where each reference becomes a link to `#ref-D6`, so that the renderer can draw a chip.
 * While the answer streams, a chip waits for its item. Once it has ended, a reference with no
 * matching item stays plain text.
 */
export function linkReferences(text: string, citations: Citation[], sources: WebSource[], ended: boolean): string {
  return text.replace(REFERENCE, (whole, kind: string, n: string) => {
    const id = `${kind}${n}`;
    return ended && !findReference(id, citations, sources) ? whole : `[${id}](#ref-${id})`;
  });
}

/** The references of a finished answer that match no citation and no source: a backend bug. */
export function unmatchedReferences(text: string, citations: Citation[], sources: WebSource[]): string[] {
  const ids = [...text.matchAll(REFERENCE)].map((m) => `${m[1]}${m[2]}`);
  return [...new Set(ids)].filter((id) => !findReference(id, citations, sources));
}

/** The references in the text, in order and without repeats: `["D6", "W1"]`. */
export function referencesIn(text: string): string[] {
  return [...new Set([...text.matchAll(REFERENCE)].map((m) => `${m[1]}${m[2]}`))];
}

export function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}
