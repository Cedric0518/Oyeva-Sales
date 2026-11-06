import { useEffect, useId, useRef, type KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import type { Origin, Provenance, StepEvent } from '../../api/types';
import { formatMonth } from '../../format';
import { ProvenanceBadge } from './ProvenanceBadge';
import styles from './Drawer.module.css';

interface DrawerProps {
  title: string;
  provenance: Provenance;
  origin: Origin;
  steps: StepEvent[];
  onClose: () => void;
}

const FOCUSABLE = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

/**
 * Certified: metric name, version and definition. Exploratory: the code that ran. Market: benchmark,
 * source and latest month published. Escape closes it; focus stays inside while it is open.
 */
export function HowCalculatedDrawer({ title, provenance, origin, steps, onClose }: DrawerProps) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const close = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    close.current?.focus();
  }, []);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== 'Tab' || !panel.current) return;
    const items = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    const first = items[0];
    const last = items.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return createPortal(
    <div className={styles.layer}>
      <div className={styles.backdrop} onClick={onClose} aria-hidden="true" />
      <div
        ref={panel}
        className={styles.drawer}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={onKeyDown}
      >
        <div className={styles.head}>
          <h2 id={titleId} className={styles.title}>
            How was this calculated
          </h2>
          <button ref={close} type="button" className={styles.close} onClick={onClose} aria-label="Close">
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <div className={styles.body}>
          <div className={styles.subject}>
            <ProvenanceBadge provenance={provenance} />
            <p className={styles.subjectTitle}>{title}</p>
          </div>
          <Explanation provenance={provenance} origin={origin} steps={steps} />
        </div>
      </div>
    </div>,
    document.body,
  );
}

function Explanation({ provenance, origin, steps }: Omit<DrawerProps, 'title' | 'onClose'>) {
  if (provenance === 'exploratory') {
    const codes = steps.filter((step) => step.tool === 'code' && step.code).map((step) => step.code ?? '');
    return (
      <>
        <p className={styles.text}>
          The assistant wrote this code for your question and ran it on your file. It is not a tested
          function: review the code before you rely on the result.
        </p>
        {codes.length === 0 ? (
          <p className={styles.muted}>The code was not sent with this answer.</p>
        ) : (
          codes.map((code, i) => (
            <section key={i} aria-label={codes.length > 1 ? `Code ${i + 1}` : 'Code'}>
              {codes.length > 1 && <h3 className={styles.label}>Code {i + 1}</h3>}
              <pre className={styles.code}>
                <code>{code}</code>
              </pre>
            </section>
          ))
        )}
      </>
    );
  }

  if (provenance === 'market') {
    return (
      <>
        <p className={styles.text}>
          Official statistics from Statistics Canada, fetched by code. Your own figures come from your file.
        </p>
        <dl className={styles.facts}>
          <dt>Benchmark</dt>
          <dd>{origin.benchmark ?? 'Not given'}</dd>
          <dt>Source</dt>
          <dd>{origin.source ?? 'Not given'}</dd>
          <dt>Latest month published</dt>
          <dd>{origin.published ? formatMonth(origin.published) : 'Not given'}</dd>
        </dl>
      </>
    );
  }

  // Certified. The definition may come with the chart or only with the step that ran the metric.
  const metric = origin.metric;
  const definition =
    metric?.definition ??
    steps.find((step) => step.metric?.name === metric?.name && step.metric?.definition)?.metric?.definition;
  return (
    <>
      <p className={styles.text}>Computed by a tested function with a fixed definition. The same file always gives the same result.</p>
      <dl className={styles.facts}>
        <dt>Metric</dt>
        <dd className={styles.mono}>{metric?.name ?? 'Not given'}</dd>
        <dt>Version</dt>
        <dd>{metric?.version ?? 'Not given'}</dd>
        <dt>Definition</dt>
        <dd>{definition ?? 'Not given'}</dd>
      </dl>
    </>
  );
}
