import type { ChatEvent, ChatEventType } from './types';

const EVENT_TYPES: ReadonlySet<string> = new Set<ChatEventType>([
  'start',
  'step',
  'text',
  'chart',
  'table',
  'citations',
  'sources',
  'blocked',
  'error',
  'done',
]);

/**
 * Reads Server-Sent Events as they arrive. `EventSource` cannot POST, so the chat reads the
 * response body itself and feeds each chunk here. A chunk can stop anywhere, even inside a line
 * or a UTF-8 character: what is not a full event yet waits for the next chunk.
 */
export class SseParser {
  private buffer = '';
  /** A chunk that ends with `\r` may be cut inside `\r\n`: the `\r` waits for the next chunk. */
  private carriageReturn = false;

  /** The events completed by this chunk. */
  feed(chunk: string): ChatEvent[] {
    let text = this.carriageReturn ? `\r${chunk}` : chunk;
    this.carriageReturn = text.endsWith('\r');
    if (this.carriageReturn) text = text.slice(0, -1);
    this.buffer += text.replace(/\r\n?/g, '\n');
    const events: ChatEvent[] = [];
    let end = this.buffer.indexOf('\n\n');
    while (end !== -1) {
      const block = this.buffer.slice(0, end);
      this.buffer = this.buffer.slice(end + 2);
      const event = parseBlock(block);
      if (event) events.push(event);
      end = this.buffer.indexOf('\n\n');
    }
    return events;
  }

  /** An event the stream ended without its blank line. */
  finish(): ChatEvent[] {
    const rest = this.carriageReturn ? `${this.buffer}\n` : this.buffer;
    this.carriageReturn = false;
    this.buffer = '';
    const event = rest.trim() ? parseBlock(rest) : null;
    return event ? [event] : [];
  }
}

function parseBlock(block: string): ChatEvent | null {
  let type = 'message';
  const data: string[] = [];
  for (const line of block.split('\n')) {
    if (line === '' || line.startsWith(':')) continue; // a comment, such as a keep-alive
    const colon = line.indexOf(':');
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? '' : line.slice(colon + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    if (field === 'event') type = value;
    else if (field === 'data') data.push(value);
  }
  if (!EVENT_TYPES.has(type)) return null;
  try {
    return { type, data: JSON.parse(data.join('\n') || '{}') } as ChatEvent;
  } catch {
    console.warn(`Unreadable data in the "${type}" event: backend bug.`);
    return null;
  }
}

/** Decodes a streamed body into events, chunk by chunk. */
export async function* readEvents(body: ReadableStream<Uint8Array>): AsyncGenerator<ChatEvent> {
  const parser = new SseParser();
  const decoder = new TextDecoder();
  const reader = body.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      yield* parser.feed(decoder.decode(value, { stream: true }));
    }
    yield* parser.feed(decoder.decode());
    yield* parser.finish();
  } finally {
    reader.releaseLock();
  }
}
