import { afterEach, describe, expect, it, vi } from 'vitest';
import { scenarioEvents } from '../api/mock/chatScenarios';
import type { ChartEvent, ChatEvent } from '../api/types';
import { conversationReducer, EMPTY, type AssistantTurn, type Conversation } from './conversation';

function play(events: ChatEvent[], state: Conversation = EMPTY, question = 'How much did I sell in 2025?'): Conversation {
  let next = conversationReducer(state, { type: 'asked', id: `q${state.turns.length}`, text: question });
  for (const event of events) next = conversationReducer(next, { type: 'event', event });
  return next;
}

function answerOf(state: Conversation): AssistantTurn {
  const last = state.turns.at(-1);
  if (last?.role !== 'assistant') throw new Error('No answer.');
  return last;
}

const CHART: ChartEvent = {
  id: 'c1',
  provenance: 'certified',
  chart: { type: 'bar', title: 'Sales', x: { label: 'Month', values: ['2025-01'] }, series: [{ name: 'Sales', values: [1] }], unit: 'CAD' },
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe('conversationReducer', () => {
  it('builds the answer of the Documents scenario from its events', () => {
    const state = play(scenarioEvents('documents', 1));
    const answer = answerOf(state);

    expect(state.streaming).toBe(false);
    expect(state.conversationId).toBe('conv_demo');
    expect(state.turns[0]).toMatchObject({ role: 'user', text: 'How much did I sell in 2025?' });
    expect(answer.status).toBe('done');
    expect(answer.text).toContain('[D6]');
    expect(answer.charts).toHaveLength(1);
    expect(answer.citations?.covered).toBe(true);
    expect(answer.citations?.items[0]?.id).toBe('D6');
  });

  it('streams until done, and updates a step by its id', () => {
    const running: ChatEvent = { type: 'step', data: { id: 's1', tool: 'certified', label: 'Sales', status: 'running' } };
    const done: ChatEvent = { type: 'step', data: { id: 's1', tool: 'certified', label: 'Sales', status: 'done' } };
    const state = play([{ type: 'start', data: { conversation_id: 'conv_1', message_id: 'msg_01' } }, running, done]);

    expect(state.streaming).toBe(true);
    expect(answerOf(state).steps).toEqual([done.data]);
  });

  it('refuses a chart or a table labelled documents or context, as a backend bug', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const state = play([
      { type: 'chart', data: { ...CHART, provenance: 'documents' } },
      { type: 'table', data: { id: 't1', provenance: 'context', title: 'News', columns: ['a'], rows: [['b']] } },
      { type: 'chart', data: CHART },
    ]);

    expect(answerOf(state).charts).toEqual([CHART]);
    expect(answerOf(state).tables).toEqual([]);
    expect(warn).toHaveBeenCalledTimes(2);
  });

  it('warns once the answer is done about a reference that matches nothing', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    play([
      { type: 'text', data: { delta: 'Closed [D6], see [W2].' } },
      { type: 'citations', data: { covered: true, items: [{ id: 'D6', doc: 'notes.md', section: 'Closures', excerpt: '...', score: null }] } },
      { type: 'done', data: {} },
    ]);

    expect(warn).toHaveBeenCalledOnce();
    expect(warn.mock.calls[0]?.[0]).toContain('[W2]');
  });

  it('keeps a blocked answer blocked when done follows', () => {
    const state = play(scenarioEvents('blocked', 1));
    expect(answerOf(state)).toMatchObject({ status: 'blocked', notice: 'This request was blocked by the safety system.' });
    expect(state.streaming).toBe(false);
  });

  it('stops on an error event and takes no more events', () => {
    const state = play([
      { type: 'start', data: { conversation_id: null, message_id: 'msg_01' } },
      { type: 'error', data: { code: 'internal', message: 'The assistant is not available right now.' } },
      { type: 'text', data: { delta: 'late' } },
    ]);

    expect(answerOf(state)).toMatchObject({ status: 'error', notice: 'The assistant is not available right now.', text: '' });
    expect(state.streaming).toBe(false);
  });

  it('sends the latest conversation id, even after an error started a new one', () => {
    const first = play(scenarioEvents('certified', 1));
    expect(first.conversationId).toBe('conv_demo');
    const second = play([{ type: 'start', data: { conversation_id: 'conv_new', message_id: 'msg_01' } }], first);
    expect(second.conversationId).toBe('conv_new');
    expect(second.turns).toHaveLength(4);
  });

  it('ends a streaming answer when the stream fails', () => {
    const state = conversationReducer(play([{ type: 'text', data: { delta: 'You sold' } }]), {
      type: 'failed',
      message: 'Could not reach the server.',
    });

    expect(answerOf(state)).toMatchObject({ status: 'error', notice: 'Could not reach the server.', text: 'You sold' });
    expect(state.streaming).toBe(false);
  });
});
