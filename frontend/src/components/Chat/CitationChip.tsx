import { useEffect, useId, useRef, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { domainOf, type Reference } from '../../chat/references';
import { cx } from '../../cx';
import styles from './Citations.module.css';

/**
 * A `[D6]` or `[W1]` reference in the answer. Until its citation or source arrives the chip waits;
 * then a click opens the popover. Escape and a click outside close it.
 */
export function CitationChip({ id, reference }: { id: string; reference: Reference | null }) {
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLSpanElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const popoverId = useId();
  const kind = id.startsWith('D') ? styles.document : styles.web;

  useEffect(() => {
    if (!open) return;
    function onPointer(event: PointerEvent) {
      if (!wrap.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      setOpen(false);
      button.current?.focus();
    }
    document.addEventListener('pointerdown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!reference) {
    return (
      <span className={cx(styles.chip, kind, styles.waiting)} aria-label={`Reference ${id}, loading`}>
        {id}
      </span>
    );
  }

  const name = reference.kind === 'D' ? reference.item.section : reference.item.title;
  return (
    <span ref={wrap} className={styles.chipWrap}>
      <button
        ref={button}
        type="button"
        className={cx(styles.chip, kind)}
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        aria-label={`Reference ${id}: ${name}`}
        onClick={() => setOpen((value) => !value)}
      >
        {id}
      </button>
      {open && (
        <span id={popoverId} role="dialog" aria-label={`Reference ${id}`} className={styles.popover}>
          {reference.kind === 'D' ? (
            <>
              <span className={styles.popoverMeta}>{reference.item.doc}</span>
              <span className={styles.popoverTitle}>{reference.item.section}</span>
              <span className={styles.excerpt}>{reference.item.excerpt}</span>
              {reference.item.score !== null && (
                <span className={styles.popoverMeta}>Relevance {reference.item.score.toFixed(2)}</span>
              )}
            </>
          ) : (
            <>
              <span className={styles.popoverTitle}>{reference.item.title}</span>
              <span className={styles.popoverMeta}>
                {domainOf(reference.item.url)}
                {reference.item.published && ` · ${reference.item.published}`}
              </span>
              <a className={styles.link} href={reference.item.url} target="_blank" rel="noopener noreferrer">
                Open the source
                <ExternalLink size={14} aria-hidden="true" />
                <span className={styles.visuallyHidden}> (opens in a new tab)</span>
              </a>
            </>
          )}
        </span>
      )}
    </span>
  );
}
