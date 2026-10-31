import type { ReactNode } from 'react';
import { CircleAlert, Info, TriangleAlert } from 'lucide-react';
import { cx } from '../../cx';
import styles from './Notice.module.css';

const ICONS = { error: CircleAlert, warning: TriangleAlert, info: Info } as const;

interface NoticeProps {
  tone: keyof typeof ICONS;
  title?: string;
  children?: ReactNode;
  /** `alert` for errors that appear after an action, so screen readers announce them. */
  role?: 'alert' | 'status';
  className?: string;
}

export function Notice({ tone, title, children, role, className }: NoticeProps) {
  const Icon = ICONS[tone];
  return (
    <div className={cx(styles.notice, styles[tone], className)} role={role}>
      <Icon size={18} aria-hidden="true" className={styles.icon} />
      <div className={styles.body}>
        {title && <p className={styles.title}>{title}</p>}
        {children}
      </div>
    </div>
  );
}
