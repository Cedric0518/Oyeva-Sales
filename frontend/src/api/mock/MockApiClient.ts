import { ApiError, type ApiClient, type UploadRequest } from '../client';
import type { ContextDocument, Dataset } from '../types';
import { contextFormatOf, validateContextFile, validateSalesFile } from '../../upload/validation';
import { EXAMPLE_CONTEXT, UPLOAD_EXAMPLE } from './uploadExample';

export interface MockOptions {
  /** How long an upload takes, so the loading state shows. */
  delayMs?: number;
}

const STATUS = { unsupported_format: 415, file_too_large: 413 } as const;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * The mock backend. Any sales file returns the contract example (Atlas values), with the file
 * name, province and document that were sent. An empty file is refused as unreadable, which is
 * how to see that error on screen.
 */
export class MockApiClient implements ApiClient {
  private readonly delayMs: number;

  constructor({ delayMs = 900 }: MockOptions = {}) {
    this.delayMs = delayMs;
  }

  async health(): Promise<{ status: 'ok' }> {
    return { status: 'ok' };
  }

  async upload({ file, region, context }: UploadRequest): Promise<Dataset> {
    await wait(this.delayMs);

    // The server checks again what the browser already checked.
    const problem = validateSalesFile(file) ?? (context ? validateContextFile(context) : null);
    if (problem) throw new ApiError(problem.code, problem.message, STATUS[problem.code]);

    if (file.size === 0) {
      throw new ApiError(
        'unreadable_file',
        `We could not read "${file.name}": the file is empty. Check that it opens in Excel, then upload it again.`,
        422,
      );
    }

    const dataset = structuredClone(UPLOAD_EXAMPLE);
    dataset.file_name = file.name;
    if (file.name.toLowerCase().endsWith('.csv')) dataset.sheets = [];
    dataset.region = region;
    dataset.context = context ? documentFor(context) : null;
    return dataset;
  }

  async sample(): Promise<Dataset> {
    await wait(this.delayMs);
    // docs/contract.md, section 6: the sample comes with atlas_context.md, region ON.
    const dataset = structuredClone(UPLOAD_EXAMPLE);
    dataset.context = { ...structuredClone(EXAMPLE_CONTEXT), name: 'atlas_context.md', format: 'md', converted: false };
    return dataset;
  }
}

function documentFor(file: File): ContextDocument {
  const format = contextFormatOf(file.name) ?? 'md';
  return { ...structuredClone(EXAMPLE_CONTEXT), name: file.name, format, converted: format !== 'md' };
}
