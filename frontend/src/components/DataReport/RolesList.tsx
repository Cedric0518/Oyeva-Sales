import { ROLE_NAMES, type Roles } from '../../api/types';
import { Notice } from '../ui/Notice';
import { ROLE_LABEL } from './labels';
import styles from './DataReport.module.css';

/** The roles certified metrics cannot run without (docs/contract.md, section 5). */
const REQUIRED = ['date', 'amount'] as const;

export function RolesList({ roles }: { roles: Roles }) {
  const missing = REQUIRED.filter((role) => !roles[role]);

  return (
    <section className={styles.section} aria-labelledby="roles-title">
      <div className={styles.sectionHead}>
        <h3 id="roles-title" className={styles.sectionTitle}>
          Column roles
        </h3>
        <span className={styles.sectionMeta}>The column used for each role</span>
      </div>

      {missing.length > 0 && (
        <Notice tone="error" title={`No ${missing.join(' or ')} column recognized`}>
          <p>
            Certified metrics need a date column and an amount column. They will refuse to run on this file until
            both are found.
          </p>
        </Notice>
      )}

      <dl className={styles.roles}>
        {ROLE_NAMES.map((role) => {
          const column = roles[role] ?? null;
          return (
            <div key={role} className={styles.role}>
              <dt className={styles.roleName}>{ROLE_LABEL[role]}</dt>
              <dd>
                {column ? <code className={styles.column}>{column}</code> : <span className={styles.notFound}>Not found</span>}
              </dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
}
