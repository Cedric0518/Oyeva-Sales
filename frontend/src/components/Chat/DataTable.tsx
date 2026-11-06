import type { Cell } from '../../api/types';
import { cx } from '../../cx';
import { formatNumber } from '../../format';
import styles from './Results.module.css';

/** A result table. Numbers are right-aligned; an empty cell says so. */
export function DataTable({ title, columns, rows }: { title: string; columns: string[]; rows: Cell[][] }) {
  const numeric = columns.map((_, c) => rows.some((row) => typeof row[c] === 'number'));
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <caption className={styles.visuallyHidden}>{title}</caption>
        <thead>
          <tr>
            {columns.map((name, c) => (
              <th key={`${name}-${c}`} scope="col" className={cx(numeric[c] && styles.number)}>
                {name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {columns.map((name, c) => (
                <td key={`${name}-${c}`} className={cx(numeric[c] && styles.number)}>
                  <CellValue cell={row[c]} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CellValue({ cell }: { cell: Cell | undefined }) {
  if (cell === null || cell === undefined) return <span className={styles.empty}>No data</span>;
  if (typeof cell === 'number') return <>{formatNumber(cell)}</>;
  if (typeof cell === 'boolean') return <>{cell ? 'Yes' : 'No'}</>;
  return <>{cell}</>;
}
