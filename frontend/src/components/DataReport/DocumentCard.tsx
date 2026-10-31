import { FileText } from 'lucide-react';
import type { ContextDocument } from '../../api/types';
import { plural } from '../../format';
import { Notice } from '../ui/Notice';
import { FORMAT_LABEL, MODE_LABEL } from './labels';
import styles from './DataReport.module.css';

export function DocumentCard({ document }: { document: ContextDocument | null }) {
  return (
    <section className={styles.section} aria-labelledby="document-title">
      <div className={styles.sectionHead}>
        <h3 id="document-title" className={styles.sectionTitle}>
          Your document
        </h3>
      </div>
      {document ? <DocumentDetails document={document} /> : <NoDocument />}
    </section>
  );
}

function NoDocument() {
  return (
    <div className={styles.empty}>
      <p className={styles.emptyTitle}>No document added</p>
      <p className={styles.muted}>
        With a document about your business, answers can explain closures, promotions or policies, and cite the
        section they use. To add one, start a new session.
      </p>
    </div>
  );
}

function DocumentDetails({ document }: { document: ContextDocument }) {
  const mode = MODE_LABEL[document.mode];
  const removed = document.removed_sections;

  return (
    <div className={styles.document}>
      <p className={styles.documentName}>
        <FileText size={18} aria-hidden="true" />
        <span>{document.name}</span>
      </p>
      <ul className={styles.tags} aria-label="Format">
        <li className={styles.tag}>{FORMAT_LABEL[document.format]}</li>
        {document.converted && document.format !== 'md' && (
          <li className={styles.tag}>Converted from {FORMAT_LABEL[document.format]}</li>
        )}
      </ul>

      <dl className={styles.facts}>
        <div className={styles.fact}>
          <dt>Sections</dt>
          <dd className="tabular">{document.sections.length}</dd>
        </div>
        <div className={styles.fact}>
          <dt>Mode</dt>
          <dd>
            {mode.name}
            <span className={styles.factNote}>{mode.explanation}</span>
          </dd>
        </div>
        <div className={styles.fact}>
          <dt>Set aside</dt>
          <dd>{removed.length === 0 ? 'None' : plural(removed.length, 'section')}</dd>
        </div>
      </dl>

      {removed.length > 0 && (
        <Notice tone="warning" title={`${plural(removed.length, 'section')} set aside at upload`}>
          <p>They are not used in answers.</p>
          <ul className={styles.removed}>
            {removed.map((section) => (
              <li key={section.id}>
                <span className={styles.sectionId}>{section.id}</span> <strong>{section.title}</strong>:{' '}
                {section.reason}
              </li>
            ))}
          </ul>
        </Notice>
      )}

      {document.sections.length > 0 && (
        <details className={styles.sectionsList}>
          <summary>Show the {plural(document.sections.length, 'section')}</summary>
          <ol>
            {document.sections.map((section) => (
              <li key={section.id}>
                <span className={styles.sectionId}>{section.id}</span>
                <span>{section.title}</span>
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
