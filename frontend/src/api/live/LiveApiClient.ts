import { ApiError, NETWORK_ERROR_MESSAGE, type ApiClient, type UploadRequest } from '../client';
import type { ContractErrorCode, Dataset } from '../types';

const CONTRACT_CODES: ReadonlySet<string> = new Set<ContractErrorCode>([
  'unsupported_format',
  'file_too_large',
  'unreadable_file',
  'missing_session',
  'dataset_not_found',
  'rate_limited',
  'internal',
]);

/** The real backend (docs/contract.md). Every call carries the `X-Session-Id` header. */
export class LiveApiClient implements ApiClient {
  private readonly baseUrl: string;
  private readonly sessionId: string;
  private readonly fetchFn: typeof fetch;

  constructor(baseUrl: string, sessionId: string, fetchFn: typeof fetch = globalThis.fetch.bind(globalThis)) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.sessionId = sessionId;
    this.fetchFn = fetchFn;
  }

  health(): Promise<{ status: 'ok' }> {
    return this.request('/api/health', { method: 'GET' });
  }

  upload({ file, region, context }: UploadRequest): Promise<Dataset> {
    const form = new FormData();
    form.append('file', file);
    form.append('region', region);
    if (context) form.append('context', context);
    return this.request('/api/upload', { method: 'POST', body: form });
  }

  sample(): Promise<Dataset> {
    return this.request('/api/sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample: 'atlas' }),
    });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('X-Session-Id', this.sessionId);

    let response: Response;
    try {
      response = await this.fetchFn(`${this.baseUrl}${path}`, { ...init, headers });
    } catch {
      throw new ApiError('network', NETWORK_ERROR_MESSAGE);
    }
    if (!response.ok) throw await errorFrom(response);
    return (await response.json()) as T;
  }
}

async function errorFrom(response: Response): Promise<ApiError> {
  try {
    const body: unknown = await response.json();
    const error = (body as { error?: { code?: unknown; message?: unknown } }).error;
    if (typeof error?.code === 'string' && CONTRACT_CODES.has(error.code) && typeof error.message === 'string') {
      return new ApiError(error.code as ContractErrorCode, error.message, response.status);
    }
  } catch {
    // Not the contract's error body: fall through.
  }
  return new ApiError('internal', `The server answered with an error (HTTP ${response.status}). Please try again.`, response.status);
}
