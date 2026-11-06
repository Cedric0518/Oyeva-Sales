import { useRef, useState, type ReactNode } from 'react';
import { Info } from 'lucide-react';
import type { Origin, Provenance, StepEvent } from '../../api/types';
import { formatMonth } from '../../format';
import { Button } from '../ui/Button';
import { HowCalculatedDrawer } from './HowCalculatedDrawer';
import { ProvenanceBadge } from './ProvenanceBadge';
import styles from './Results.module.css';

interface ResultCardProps {
  provenance: Provenance;
  title: string;
  origin: Origin;
  /** The steps of the answer: the drawer finds the code that ran, or a metric definition, there. */
  steps: StepEvent[];
  children: ReactNode;
}

/** The frame of a chart or a table: provenance label top left, "How was this calculated" on the right. */
export function ResultCard({ provenance, title, origin, steps, children }: ResultCardProps) {
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null);

  return (
    <figure className={styles.card}>
      <div className={styles.cardHead}>
        <ProvenanceBadge provenance={provenance} />
        <Button ref={opener} variant="ghost" className={styles.howButton} onClick={() => setOpen(true)}>
          <Info size={16} aria-hidden="true" />
          How was this calculated
        </Button>
      </div>
      <figcaption className={styles.cardTitle}>{title}</figcaption>
      {children}
      {provenance === 'market' && (
        <p className={styles.marketLine}>
          Benchmark: {origin.benchmark ?? 'not given'}. Source: {origin.source ?? 'not given'}. Latest month
          published: {origin.published ? formatMonth(origin.published) : 'not given'}.
        </p>
      )}
      {open && (
        <HowCalculatedDrawer
          title={title}
          provenance={provenance}
          origin={origin}
          steps={steps}
          onClose={() => {
            setOpen(false);
            opener.current?.focus();
          }}
        />
      )}
    </figure>
  );
}
