import { FileSpreadsheet } from 'lucide-react';
import type { Dataset } from '../../api/types';
import { formatCount, plural } from '../../format';
import { provinceName } from '../../provinces';
import { ChecksList } from './ChecksList';
import { DocumentCard } from './DocumentCard';
import { RolesList } from './RolesList';
import styles from './DataReport.module.css';

/** The dataset panel: what the upload found in the sales file and in the document. */
export function DataReport({ dataset }: { dataset: Dataset }) {
  const facts = [
    `${formatCount(dataset.rows)} rows`,
    dataset.sheets.length > 1 && `${plural(dataset.sheets.length, 'sheet')} (${dataset.sheets.join(', ')})`,
    provinceName(dataset.region),
  ].filter(Boolean);

  return (
    <aside className={styles.report} aria-labelledby="report-title">
      <div className={styles.header}>
        <h2 id="report-title" className={styles.title}>
          Data report
        </h2>
        <p className={styles.fileName}>
          <FileSpreadsheet size={18} aria-hidden="true" />
          <span>{dataset.file_name}</span>
        </p>
        <p className={styles.fileFacts}>{facts.join(' · ')}</p>
      </div>
      <ChecksList checks={dataset.checks} />
      <RolesList roles={dataset.roles} />
      <DocumentCard document={dataset.context} />
    </aside>
  );
}
