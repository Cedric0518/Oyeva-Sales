import { useId, useState } from 'react';
import { Check, ChevronDown, ChevronRight, LoaderCircle, X } from 'lucide-react';
import type { StepEvent, StepStatus } from '../../api/types';
import { STATUSES, TOOLS } from '../../chat/labels';
import { cx } from '../../cx';
import styles from './Chat.module.css';

const ICONS: Record<StepStatus, typeof Check> = { running: LoaderCircle, done: Check, failed: X };

/** The tools the assistant used, collapsed by default, each with its status in words. */
export function StepsTimeline({ steps }: { steps: StepEvent[] }) {
  const [open, setOpen] = useState(false);
  const listId = useId();
  if (steps.length === 0) return null;

  const tools = [...new Set(steps.map((step) => TOOLS[step.tool]))].join(', ');
  const Chevron = open ? ChevronDown : ChevronRight;
  return (
    <div className={styles.steps}>
      <button
        type="button"
        className={styles.stepsToggle}
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((value) => !value)}
      >
        <Chevron size={16} aria-hidden="true" />
        {steps.length === 1 ? '1 step' : `${steps.length} steps`}
        <span className={styles.stepsTools}>{tools}</span>
      </button>
      <ol id={listId} className={styles.stepsList} hidden={!open}>
        {steps.map((step) => {
          const Icon = ICONS[step.status];
          return (
            <li key={step.id} className={cx(styles.step, styles[step.status])}>
              <Icon size={16} aria-hidden="true" className={cx(step.status === 'running' && styles.spin)} />
              <span className={styles.stepTool}>{TOOLS[step.tool]}</span>
              <span className={styles.stepLabel}>{step.label}</span>
              <span className={styles.stepStatus}>{STATUSES[step.status]}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
