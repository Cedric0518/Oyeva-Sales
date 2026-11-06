import type { ChartEvent, ChatEvent, Citation, StepEvent, TableEvent, WebSource } from '../api/types';
import { unmatchedReferences } from './references';

export interface UserTurn {
  role: 'user';
  id: string;
  text: string;
}

export type AnswerStatus = 'streaming' | 'done' | 'blocked' | 'error';

export interface AssistantTurn {
  role: 'assistant';
  id: string;
  status: AnswerStatus;
  steps: StepEvent[];
  text: string;
  charts: ChartEvent[];
  tables: TableEvent[];
  citations: { covered: boolean; items: Citation[] } | null;
  sources: WebSource[] | null;
  /** The blocked or error message, shown as is. */
  notice: string | null;
}

export type Turn = UserTurn | AssistantTurn;

export interface Conversation {
  turns: Turn[];
  /** The latest one received in a `start` event: sent with the next message. */
  conversationId: string | null;
  streaming: boolean;
}

export type ConversationAction =
  | { type: 'asked'; id: string; text: string }
  | { type: 'event'; event: ChatEvent }
  | { type: 'failed'; message: string };

export const EMPTY: Conversation = { turns: [], conversationId: null, streaming: false };

/** `documents` and `context` never go on a chart or a table (docs/contract.md, section 2). */
const NOT_FOR_CHARTS = new Set(['documents', 'context']);

export function conversationReducer(state: Conversation, action: ConversationAction): Conversation {
  switch (action.type) {
    case 'asked': {
      const answer: AssistantTurn = {
        role: 'assistant',
        id: `${action.id}-answer`,
        status: 'streaming',
        steps: [],
        text: '',
        charts: [],
        tables: [],
        citations: null,
        sources: null,
        notice: null,
      };
      return { ...state, streaming: true, turns: [...state.turns, { role: 'user', id: action.id, text: action.text }, answer] };
    }
    case 'event': {
      const { event } = action;
      // Always the latest one received, even null: the API then starts a new conversation.
      const conversationId = event.type === 'start' ? event.data.conversation_id : state.conversationId;
      // An answer that was blocked or that failed takes no more events; `done` closes it anyway.
      const turns = updateAnswer(state.turns, (answer) => (answer.status === 'streaming' ? applyEvent(answer, event) : answer));
      const answer = lastAnswer(turns);
      return { turns, conversationId, streaming: answer?.status === 'streaming' };
    }
    case 'failed': {
      const turns = updateAnswer(state.turns, (answer) =>
        answer.status === 'streaming' ? { ...answer, status: 'error', notice: action.message } : answer,
      );
      return { ...state, turns, streaming: false };
    }
  }
}

export function applyEvent(answer: AssistantTurn, event: ChatEvent): AssistantTurn {
  switch (event.type) {
    case 'start':
      return answer;
    case 'step': {
      const index = answer.steps.findIndex((step) => step.id === event.data.id);
      const steps = index === -1 ? [...answer.steps, event.data] : answer.steps.map((s, i) => (i === index ? event.data : s));
      return { ...answer, steps };
    }
    case 'text':
      return { ...answer, text: answer.text + event.data.delta };
    case 'chart':
      if (NOT_FOR_CHARTS.has(event.data.provenance)) {
        console.warn(`A chart with provenance "${event.data.provenance}" is not shown: backend bug.`);
        return answer;
      }
      return { ...answer, charts: [...answer.charts, event.data] };
    case 'table':
      if (NOT_FOR_CHARTS.has(event.data.provenance)) {
        console.warn(`A table with provenance "${event.data.provenance}" is not shown: backend bug.`);
        return answer;
      }
      return { ...answer, tables: [...answer.tables, event.data] };
    case 'citations':
      return { ...answer, citations: event.data };
    case 'sources':
      return { ...answer, sources: event.data.items };
    case 'blocked':
      return { ...answer, status: 'blocked', notice: event.data.message };
    case 'error':
      return { ...answer, status: 'error', notice: event.data.message };
    case 'done': {
      for (const id of unmatchedReferences(answer.text, answer.citations?.items ?? [], answer.sources ?? [])) {
        console.warn(`Reference [${id}] has no matching ${id.startsWith('D') ? 'citation' : 'source'}: backend bug.`);
      }
      return answer.status === 'streaming' ? { ...answer, status: 'done' } : answer;
    }
  }
}

function lastAnswer(turns: Turn[]): AssistantTurn | undefined {
  const last = turns.at(-1);
  return last?.role === 'assistant' ? last : undefined;
}

function updateAnswer(turns: Turn[], update: (answer: AssistantTurn) => AssistantTurn): Turn[] {
  const answer = lastAnswer(turns);
  return answer ? [...turns.slice(0, -1), update(answer)] : turns;
}
