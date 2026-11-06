import { useId } from 'react';
import type { Provenance } from '../../api/types';
import { PROVENANCE } from '../../chat/labels';
import { cx } from '../../cx';
import styles from './ProvenanceBadge.module.css';

/** One of the five labels, with its tooltip on hover and on keyboard focus. */
export function ProvenanceBadge({ provenance }: { provenance: Provenance }) {
  const tooltipId = useId();
  const { label, tooltip } = PROVENANCE[provenance];
  return (
    <span className={styles.wrap}>
      <span className={cx(styles.badge, styles[provenance])} tabIndex={0} aria-describedby={tooltipId}>
        {label}
      </span>
      <span role="tooltip" id={tooltipId} className={styles.tooltip}>
        {tooltip}
      </span>
    </span>
  );
}
