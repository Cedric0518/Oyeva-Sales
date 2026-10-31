import { MessagesSquare } from 'lucide-react';
import type { Cell, Dataset } from '../../api/types';
import { cx } from '../../cx';
import { DataReport } from '../DataReport/DataReport';
import styles from './Workspace.module.css';

/** After the upload: the dataset panel on the left, the chat on the right (F2). */
export function Workspace({ dataset }: { dataset: Dataset }) {
  return (
    <div className={styles.workspace}>
      <DataReport dataset={dataset} />
      <section className={styles.main} aria-label="Conversation">
        <div className={styles.placeholder}>
          <MessagesSquare size={24} aria-hidden="true" />
          <h2 className={styles.placeholderTitle}>Questions open here soon</h2>
          <p className={styles.muted}>
            The chat comes with the next milestone (F2). For now, review the data report on the left.
          </p>
        </div>
        <FilePreview dataset={dataset} />
      </section>
    </div>
  );
}

function FilePreview({ dataset }: { dataset: Dataset }) {
  const { columns, rows } = dataset.preview;
  const numeric = new Set(dataset.columns.filter((c) => c.type === 'number').map((c) => c.name));
  if (columns.length === 0) return null;

  return (
    <section className={styles.preview} aria-labelledby="preview-title">
      <div className={styles.previewHead}>
        <h2 id="preview-title" className={styles.previewTitle}>
          First rows
        </h2>
        <span className={styles.muted}>{dataset.file_name}</span>
      </div>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((name) => (
                <th key={name} scope="col" className={cx(numeric.has(name) && styles.number)}>
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr key={r}>
                {columns.map((name, c) => (
                  <td key={name} className={cx(numeric.has(name) && styles.number)}>
                    {display(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function display(cell: Cell | undefined): string {
  if (cell === null || cell === undefined) return '';
  return String(cell);
}
