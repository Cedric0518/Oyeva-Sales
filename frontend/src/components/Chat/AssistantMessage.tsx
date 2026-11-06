import { lazy, Suspense } from 'react';
import { LoaderCircle } from 'lucide-react';
import type { AssistantTurn } from '../../chat/conversation';
import { Notice } from '../ui/Notice';
import { AnswerText } from './AnswerText';
import { DataTable } from './DataTable';
import { ResultCard } from './ResultCard';
import { BlockedNotice, DocumentsPanel, NotCoveredNotice, WebSourcesBox } from './SourcesPanels';
import { StepsTimeline } from './StepsTimeline';
import styles from './Chat.module.css';
import resultStyles from './Results.module.css';

// ECharts is most of the bundle: it loads with the first chart, not with the upload screen.
const ChartView = lazy(() => import('./ChartView').then((module) => ({ default: module.ChartView })));

/** One answer: steps, text with references, charts, tables, documents, web sources, or why it stopped. */
export function AssistantMessage({ answer }: { answer: AssistantTurn }) {
  const streaming = answer.status === 'streaming';
  const running = answer.steps.findLast((step) => step.status === 'running');
  const citations = answer.citations;

  return (
    <article className={styles.answer} aria-label="Answer" aria-busy={streaming}>
      <StepsTimeline steps={answer.steps} />
      {answer.text && (
        <AnswerText
          text={answer.text}
          streaming={streaming}
          citations={citations?.items ?? []}
          sources={answer.sources ?? []}
        />
      )}
      {answer.charts.map((chart) => (
        <ResultCard key={chart.id} provenance={chart.provenance} title={chart.chart.title} origin={chart} steps={answer.steps}>
          <Suspense fallback={<div className={resultStyles.chart} />}>
            <ChartView spec={chart.chart} />
          </Suspense>
        </ResultCard>
      ))}
      {answer.tables.map((table) => (
        <ResultCard key={table.id} provenance={table.provenance} title={table.title} origin={table} steps={answer.steps}>
          <DataTable title={table.title} columns={table.columns} rows={table.rows} />
        </ResultCard>
      ))}
      {citations && !citations.covered && <NotCoveredNotice />}
      {citations?.covered && <DocumentsPanel items={citations.items} />}
      {answer.sources && <WebSourcesBox items={answer.sources} />}
      {answer.status === 'blocked' && <BlockedNotice message={answer.notice ?? ''} />}
      {answer.status === 'error' && (
        <Notice tone="error" title="The answer stopped" role="alert">
          <p>{answer.notice}</p>
        </Notice>
      )}
      {streaming && (
        <p className={styles.current} role="status">
          <LoaderCircle size={16} aria-hidden="true" className={styles.spin} />
          {running ? running.label : 'Working on your question'}
        </p>
      )}
    </article>
  );
}
