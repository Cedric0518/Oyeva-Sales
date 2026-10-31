import { CircleCheck, CircleX, TriangleAlert } from 'lucide-react';
import type { Check } from '../../api/types';
import { cx } from '../../cx';
import { formatCAD } from '../../format';
import { STATUS_LABEL, summarizeChecks } from './labels';
import styles from './DataReport.module.css';

const STATUS_ICON = { ok: CircleCheck, warning: TriangleAlert, error: CircleX } as const;

export function ChecksList({ checks }: { checks: Check[] }) {
  return (
    <section className={styles.section} aria-labelledby="checks-title">
      <div className={styles.sectionHead}>
        <h3 id="checks-title" className={styles.sectionTitle}>
          Checks
        </h3>
        <span className={styles.sectionMeta}>{summarizeChecks(checks)}</span>
      </div>
      <ul className={styles.checks}>
        {checks.map((check) => {
          const Icon = STATUS_ICON[check.status];
          return (
            <li key={check.id} className={styles.check}>
              <Icon size={18} aria-hidden="true" className={cx(styles.statusIcon, styles[check.status])} />
              <div className={styles.checkBody}>
                <p className={styles.checkName}>{check.name}</p>
                <p className={styles.checkDetail}>
                  <span className={cx(styles.statusWord, styles[check.status])}>{STATUS_LABEL[check.status]}</span>
                  <span aria-hidden="true"> · </span>
                  <span className="visually-hidden">: </span>
                  {check.detail}
                </p>
              </div>
              {check.amount !== null && <span className={cx(styles.amount, 'tabular')}>{formatCAD(check.amount)}</span>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
