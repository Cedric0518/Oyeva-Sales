import { afterEach, describe, expect, it, vi } from 'vitest';
import { readEvents, SseParser } from './sse';
import type { ChatEvent } from './types';

// The Documents scenario of frontend/CLAUDE.md, section 7, as the API writes it.
const STREAM = [
  'event: start',
  'data: {"conversation_id": "conv_demo", "message_id": "msg_02"}',
  '',
  'event: step',
  'data: {"id": "s2", "tool": "documents", "label": "Your documents", "status": "done"}',
  '',
  'event: text',
  'data: {"delta": "Queen Street sold $2,003.68 in March 2025 · see "}',
  '',
  'event: text',
  'data: {"delta": "your notes [D6]."}',
  '',
  'event: citations',
  'data: {"covered": true, "items": [{"id": "D6", "doc": "atlas_context.pdf", "section": "Store closures", "excerpt": "Closed from March 3 to March 28, 2025.", "score": null}]}',
  '',
  'event: done',
  'data: {}',
  '',
  '',
].join('\n');

function parseAll(chunks: string[]): ChatEvent[] {
  const parser = new SseParser();
  return [...chunks.flatMap((chunk) => parser.feed(chunk)), ...parser.finish()];
}

function bodyOf(chunks: Uint8Array[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      controller.close();
    },
  });
}

async function collect(events: AsyncIterable<ChatEvent>): Promise<ChatEvent[]> {
  const all: ChatEvent[] = [];
  for await (const event of events) all.push(event);
  return all;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('SseParser', () => {
  it('reads every event of a stream, in order, with its data', () => {
    const events = parseAll([STREAM]);
    expect(events.map((e) => e.type)).toEqual(['start', 'step', 'text', 'text', 'citations', 'done']);
    expect(events[0]).toEqual({ type: 'start', data: { conversation_id: 'conv_demo', message_id: 'msg_02' } });
    expect(events[3]).toEqual({ type: 'text', data: { delta: 'your notes [D6].' } });
  });

  it('gives the same events wherever the stream is cut', () => {
    const whole = parseAll([STREAM]);
    for (let cut = 1; cut < STREAM.length; cut += 1) {
      expect(parseAll([STREAM.slice(0, cut), STREAM.slice(cut)])).toEqual(whole);
    }
  });

  it('gives the same events when each character arrives alone', () => {
    expect(parseAll([...STREAM])).toEqual(parseAll([STREAM]));
  });

  it('reads CRLF line ends, even when a chunk stops between CR and LF', () => {
    const crlf = STREAM.replaceAll('\n', '\r\n');
    const whole = parseAll([crlf]);
    expect(whole).toEqual(parseAll([STREAM]));
    for (let cut = 1; cut < crlf.length; cut += 1) {
      expect(parseAll([crlf.slice(0, cut), crlf.slice(cut)])).toEqual(whole);
    }
  });

  it('skips comments and unknown events, and joins data written on several lines', () => {
    const events = parseAll([': keep-alive\n\nevent: ping\ndata: {}\n\nevent: text\ndata: {"delta":\ndata: "a"}\n\n']);
    expect(events).toEqual([{ type: 'text', data: { delta: 'a' } }]);
  });

  it('reads a last event that has no blank line after it', () => {
    expect(parseAll(['event: done\ndata: {}'])).toEqual([{ type: 'done', data: {} }]);
  });

  it('skips an event whose data is not JSON and says so in the console', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(parseAll(['event: text\ndata: {oops\n\nevent: done\ndata: {}\n\n'])).toEqual([{ type: 'done', data: {} }]);
    expect(warn).toHaveBeenCalledOnce();
  });
});

describe('readEvents', () => {
  it('decodes a body cut inside a UTF-8 character', async () => {
    const bytes = new TextEncoder().encode(STREAM);
    const middle = bytes.indexOf(0xc2); // first byte of "·", two bytes long
    expect(middle).toBeGreaterThan(0);
    const events = await collect(readEvents(bodyOf([bytes.slice(0, middle + 1), bytes.slice(middle + 1)])));
    expect(events).toEqual(parseAll([STREAM]));
  });
});
