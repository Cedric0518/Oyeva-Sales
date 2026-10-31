import type { Dataset, ErrorCode, ProvinceCode } from './types';

export interface UploadRequest {
  file: File;
  region: ProvinceCode;
  context: File | null;
}

/** The only door to the backend. Two implementations: MockApiClient and LiveApiClient. */
export interface ApiClient {
  health(): Promise<{ status: 'ok' }>;
  upload(request: UploadRequest): Promise<Dataset>;
  sample(): Promise<Dataset>;
}

/** An error the user can read: `message` is shown as is (docs/contract.md, section 1). */
export class ApiError extends Error {
  readonly code: ErrorCode;
  readonly status: number | null;

  constructor(code: ErrorCode, message: string, status: number | null = null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

export const NETWORK_ERROR_MESSAGE =
  'Could not reach the server. Check your connection and try again.';

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError('internal', 'Something went wrong. Please try again.');
}
