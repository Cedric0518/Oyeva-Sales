import { ExternalLink, FileQuestion, ShieldAlert } from 'lucide-react';
import type { Citation, WebSource } from '../../api/types';
import { domainOf } from '../../chat/references';
import { ProvenanceBadge } from './ProvenanceBadge';
import styles from './Chat.module.css';

/** The sections of the user's document that the answer cites. */
export function DocumentsPanel({ items }: { items: Citation[] }) {
  if (items.length === 0) return null;
  return (
    <section className={styles.panel} aria-label="Cited sections of your document">
      <div className={styles.panelHead}>
        <ProvenanceBadge provenance="documents" />
        <span className={styles.panelTitle}>Cited sections</span>
      </div>
      <ul className={styles.panelList}>
        {items.map((item) => (
          <li key={item.id} className={styles.panelItem}>
            <span className={styles.itemHead}>
              <span className={styles.itemId}>{item.id}</span>
              <span className={styles.itemTitle}>{item.section}</span>
            </span>
            <span className={styles.excerpt}>{item.excerpt}</span>
            <span className={styles.itemMeta}>
              {item.doc}
              {item.score !== null && ` · Relevance ${item.score.toFixed(2)}`}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** `citations` with `covered: false`: the document says nothing about the question. */
export function NotCoveredNotice() {
  return (
    <div className={styles.notCovered} role="status">
      <FileQuestion size={18} aria-hidden="true" />
      <span>Your document doesn't cover this.</span>
    </div>
  );
}

/** Web sources: context only, never computed from the user's data. */
export function WebSourcesBox({ items }: { items: WebSource[] }) {
  if (items.length === 0) return null;
  return (
    <section className={styles.panel} aria-label="Web sources">
      <div className={styles.panelHead}>
        <ProvenanceBadge provenance="context" />
        <span className={styles.panelTitle}>External · not computed from your data</span>
      </div>
      <ul className={styles.panelList}>
        {items.map((item) => (
          <li key={item.id} className={styles.panelItem}>
            <span className={styles.itemHead}>
              <span className={styles.itemId}>{item.id}</span>
              <a className={styles.itemLink} href={item.url} target="_blank" rel="noopener noreferrer">
                {item.title}
                <ExternalLink size={14} aria-hidden="true" />
                <span className={styles.visuallyHidden}> (opens in a new tab)</span>
              </a>
            </span>
            <span className={styles.itemMeta}>
              {domainOf(item.url)}
              {item.published && ` · ${item.published}`}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** The guardrail refused the request. */
export function BlockedNotice({ message }: { message: string }) {
  return (
    <div className={styles.blocked} role="alert">
      <ShieldAlert size={18} aria-hidden="true" />
      <div>
        <p className={styles.blockedTitle}>Request blocked</p>
        <p>{message}</p>
        <p className={styles.itemMeta}>Ask a question about your sales or your document instead.</p>
      </div>
    </div>
  );
}
