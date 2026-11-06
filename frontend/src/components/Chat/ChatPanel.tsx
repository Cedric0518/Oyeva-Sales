import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from 'react';
import { ArrowUp } from 'lucide-react';
import { SAMPLE_QUESTIONS, type ScenarioName } from '../../api/mock/chatScenarios';
import type { Dataset } from '../../api/types';
import { useConversation } from '../../chat/useConversation';
import { provinceName } from '../../provinces';
import { Button } from '../ui/Button';
import { AssistantMessage } from './AssistantMessage';
import styles from './Chat.module.css';

interface ChatPanelProps {
  dataset: Dataset;
  /** Shows the scenario picker of the mock backend, in development only. */
  mockBackend?: boolean;
  /** Shown under the starter questions until the first message. */
  children?: ReactNode;
}

/** The conversation: messages, then the input. Send is disabled while an answer streams. */
export function ChatPanel({ dataset, mockBackend = false, children }: ChatPanelProps) {
  const { turns, streaming, ask } = useConversation(dataset.dataset_id);
  const [draft, setDraft] = useState('');
  const list = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const inputId = useId();

  useEffect(() => {
    const element = list.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [turns]);

  useEffect(() => {
    if (!streaming) input.current?.focus();
  }, [streaming]);

  function send(text: string) {
    if (streaming || !text.trim()) return;
    setDraft('');
    void ask(text);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    send(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      send(draft);
    }
  }

  const starters = [
    'What are my total sales?',
    'Show my sales by month',
    'Which products sell the most?',
    `Am I doing better than ${provinceName(dataset.region)} retail?`,
    ...(dataset.context ? ['Why did my weakest month sell so little?'] : []),
  ];

  return (
    <section className={styles.chat} aria-label="Conversation">
      <div ref={list} className={styles.messages}>
        {turns.length === 0 ? (
          <div className={styles.welcome}>
            <h2 className={styles.welcomeTitle}>Ask about your sales</h2>
            <p className={styles.muted}>
              Every number in an answer says where it comes from: Certified, Exploratory, Market, Your documents or
              Context.
            </p>
            <div className={styles.starters}>
              {starters.map((question) => (
                <button key={question} type="button" className={styles.starter} onClick={() => send(question)}>
                  {question}
                </button>
              ))}
            </div>
            {mockBackend && import.meta.env.DEV && <ScenarioPicker onPick={send} />}
            {children}
          </div>
        ) : (
          turns.map((turn) =>
            turn.role === 'user' ? (
              <p key={turn.id} className={styles.question}>
                <span className={styles.visuallyHidden}>You asked: </span>
                {turn.text}
              </p>
            ) : (
              <AssistantMessage key={turn.id} answer={turn} />
            ),
          )
        )}
      </div>
      <form className={styles.composer} onSubmit={onSubmit}>
        <label htmlFor={inputId} className={styles.visuallyHidden}>
          Ask a question about your sales
        </label>
        <textarea
          ref={input}
          id={inputId}
          className={styles.input}
          rows={2}
          value={draft}
          disabled={streaming}
          placeholder={streaming ? 'The answer is being written...' : 'Ask a question about your sales'}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <Button type="submit" variant="primary" disabled={streaming || !draft.trim()} aria-label="Send">
          <ArrowUp size={18} aria-hidden="true" />
        </Button>
      </form>
    </section>
  );
}

/** Development only: one button per scenario of the mock backend. */
function ScenarioPicker({ onPick }: { onPick: (question: string) => void }) {
  const names = Object.keys(SAMPLE_QUESTIONS) as ScenarioName[];
  return (
    <div className={styles.scenarios}>
      <p className={styles.muted}>Mock backend scenarios (development only)</p>
      <div className={styles.starters}>
        {names.map((name) => (
          <button key={name} type="button" className={styles.scenario} onClick={() => onPick(SAMPLE_QUESTIONS[name])}>
            {name.replace('_', ' ')}
          </button>
        ))}
      </div>
    </div>
  );
}
