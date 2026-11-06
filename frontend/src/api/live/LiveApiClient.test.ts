import { describe, expect, it, vi } from 'vitest';
import { makeFile } from '../../test/files';
import { NETWORK_ERROR_MESSAGE } from '../client';
import { UPLOAD_EXAMPLE } from '../mock/uploadExample';
import { LiveApiClient } from './LiveApiClient';

const SESSION = '0b6f6d1e-9a1c-4c7e-8f50-2f1d3c4b5a69';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function clientWith(fetchFn: typeof fetch) {
  return new LiveApiClient('http://localhost:8000/', SESSION, fetchFn);
}

describe('LiveApiClient', () => {
  it('sends the upload as multipart, with the session header', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(UPLOAD_EXAMPLE));
    const sales = makeFile('atlas_sales.xlsx');
    const notes = makeFile('atlas_context.pdf');

    const dataset = await clientWith(fetchFn).upload({ file: sales, region: 'ON', context: notes });

    expect(dataset.dataset_id).toBe('ds_3f9a1c2b7d4e8f01');
    const [url, init] = fetchFn.mock.calls[0]!;
    expect(url).toBe('http://localhost:8000/api/upload');
    expect(init?.method).toBe('POST');
    expect(new Headers(init?.headers).get('X-Session-Id')).toBe(SESSION);
    const form = init?.body as FormData;
    expect(form.get('region')).toBe('ON');
    expect((form.get('file') as File).name).toBe('atlas_sales.xlsx');
    expect((form.get('context') as File).name).toBe('atlas_context.pdf');
  });

  it('leaves out the context field when there is no document', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(UPLOAD_EXAMPLE));
    await clientWith(fetchFn).upload({ file: makeFile('a.csv'), region: 'BC', context: null });
    const form = fetchFn.mock.calls[0]![1]?.body as FormData;
    expect(form.has('context')).toBe(false);
  });

  it('asks for the Atlas sample as JSON', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(UPLOAD_EXAMPLE));
    await clientWith(fetchFn).sample();
    const [url, init] = fetchFn.mock.calls[0]!;
    expect(url).toBe('http://localhost:8000/api/sample');
    expect(init?.body).toBe('{"sample":"atlas"}');
    const headers = new Headers(init?.headers);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('X-Session-Id')).toBe(SESSION);
  });

  it('turns a contract error body into an ApiError with its message', async () => {
    const fetchFn = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ error: { code: 'file_too_large', message: 'The file is over 20 MB.' } }, 413));
    const error = await clientWith(fetchFn)
      .upload({ file: makeFile('a.csv'), region: 'ON', context: null })
      .catch((e) => e);
    expect(error).toMatchObject({ code: 'file_too_large', message: 'The file is over 20 MB.', status: 413 });
  });

  it('falls back to a generic message when the body is not the contract error', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(new Response('Bad gateway', { status: 502 }));
    const error = await clientWith(fetchFn).health().catch((e) => e);
    expect(error).toMatchObject({ code: 'internal', status: 502 });
    expect(error.message).toContain('HTTP 502');
  });

  it('reports a network failure in plain words', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockRejectedValue(new TypeError('Failed to fetch'));
    const error = await clientWith(fetchFn).health().catch((e) => e);
    expect(error).toMatchObject({ code: 'network', message: NETWORK_ERROR_MESSAGE });
  });
});

describe('LiveApiClient.chat', () => {
  const REQUEST = { dataset_id: 'ds_3f9a1c2b7d4e8f01', conversation_id: null, message: 'How much did I sell in 2025?' };

  function streamResponse(chunks: string[], status = 200): Response {
    const encoder = new TextEncoder();
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
        controller.close();
      },
    });
    return new Response(body, { status, headers: { 'Content-Type': 'text/event-stream' } });
  }

  async function collect(events: AsyncIterable<unknown>): Promise<unknown[]> {
    const all: unknown[] = [];
    for await (const event of events) all.push(event);
    return all;
  }

  it('posts the message with the session header and reads the events as they arrive', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      streamResponse([
        'event: start\ndata: {"conversation_id": "conv_8c1e", "message_id": "msg_01"}\n\nevent: te',
        'xt\ndata: {"delta": "You sold $649,958.80 in 2025."}\n\n',
        'event: done\ndata: {}\n\n',
      ]),
    );

    const events = await collect(clientWith(fetchFn).chat(REQUEST));

    expect(events).toEqual([
      { type: 'start', data: { conversation_id: 'conv_8c1e', message_id: 'msg_01' } },
      { type: 'text', data: { delta: 'You sold $649,958.80 in 2025.' } },
      { type: 'done', data: {} },
    ]);
    const [url, init] = fetchFn.mock.calls[0] ?? [];
    expect(url).toBe('http://localhost:8000/api/chat');
    expect(init?.method).toBe('POST');
    expect(JSON.parse(String(init?.body))).toEqual(REQUEST);
    const headers = new Headers(init?.headers);
    expect(headers.get('X-Session-Id')).toBe(SESSION);
    expect(headers.get('Accept')).toBe('text/event-stream');
  });

  it('throws the contract error when the API refuses the request', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({ error: { code: 'dataset_not_found', message: 'Upload your file again.' } }, 404),
    );
    const error = await collect(clientWith(fetchFn).chat(REQUEST)).catch((e) => e);
    expect(error).toMatchObject({ code: 'dataset_not_found', message: 'Upload your file again.', status: 404 });
  });

  it('reports a network failure in plain words', async () => {
    const fetchFn = vi.fn<typeof fetch>().mockRejectedValue(new TypeError('Failed to fetch'));
    const error = await collect(clientWith(fetchFn).chat(REQUEST)).catch((e) => e);
    expect(error).toMatchObject({ code: 'network', message: NETWORK_ERROR_MESSAGE });
  });

  it('ends quietly when the user aborts', async () => {
    const controller = new AbortController();
    controller.abort();
    const fetchFn = vi.fn<typeof fetch>().mockRejectedValue(new DOMException('Aborted', 'AbortError'));
    expect(await collect(clientWith(fetchFn).chat(REQUEST, controller.signal))).toEqual([]);
  });
});
