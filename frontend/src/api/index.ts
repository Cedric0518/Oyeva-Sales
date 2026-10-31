import type { ApiClient } from './client';
import { LiveApiClient } from './live/LiveApiClient';
import { MockApiClient } from './mock/MockApiClient';
import { sessionId } from './session';

export type ApiMode = 'mock' | 'live';

/** `VITE_API_MODE`: `mock` (default) or `live`. */
export function apiMode(): ApiMode {
  return import.meta.env.VITE_API_MODE === 'live' ? 'live' : 'mock';
}

export function createApiClient(mode: ApiMode = apiMode()): ApiClient {
  if (mode === 'live') {
    return new LiveApiClient(import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', sessionId);
  }
  return new MockApiClient();
}
