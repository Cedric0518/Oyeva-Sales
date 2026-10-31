import { describe, expect, it } from 'vitest';
import { makeFile } from '../../test/files';
import { ApiError } from '../client';
import { MockApiClient } from './MockApiClient';
import { UPLOAD_EXAMPLE } from './uploadExample';

const api = new MockApiClient({ delayMs: 0 });

describe('MockApiClient.upload', () => {
  it('returns the contract example with the file name and province that were sent', async () => {
    const dataset = await api.upload({ file: makeFile('my_sales.xlsx'), region: 'QC', context: null });
    expect(dataset.file_name).toBe('my_sales.xlsx');
    expect(dataset.region).toBe('QC');
    expect(dataset.rows).toBe(59764);
    expect(dataset.checks).toEqual(UPLOAD_EXAMPLE.checks);
    expect(dataset.context).toBeNull();
  });

  it('describes the document that was sent', async () => {
    const pdf = await api.upload({ file: makeFile('a.xlsx'), region: 'ON', context: makeFile('notes.pdf') });
    expect(pdf.context).toMatchObject({ name: 'notes.pdf', format: 'pdf', converted: true, mode: 'full' });

    const md = await api.upload({ file: makeFile('a.xlsx'), region: 'ON', context: makeFile('notes.md') });
    expect(md.context).toMatchObject({ name: 'notes.md', format: 'md', converted: false });
  });

  it('has no sheets for a CSV file', async () => {
    const dataset = await api.upload({ file: makeFile('orders.csv'), region: 'ON', context: null });
    expect(dataset.sheets).toEqual([]);
  });

  it('refuses an empty file as unreadable', async () => {
    const error = await api.upload({ file: makeFile('empty.csv', 0), region: 'ON', context: null }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: 'unreadable_file', status: 422 });
  });

  it('checks the format again, as the server does', async () => {
    const error = await api.upload({ file: makeFile('notes.pdf'), region: 'ON', context: null }).catch((e) => e);
    expect(error).toMatchObject({ code: 'unsupported_format', status: 415 });
  });

  it('does not share state between calls', async () => {
    const first = await api.upload({ file: makeFile('one.xlsx'), region: 'ON', context: null });
    first.checks.length = 0;
    const second = await api.upload({ file: makeFile('two.xlsx'), region: 'ON', context: null });
    expect(second.checks).toHaveLength(8);
    expect(UPLOAD_EXAMPLE.file_name).toBe('atlas_sales.xlsx');
  });
});

describe('MockApiClient.sample', () => {
  it('returns Atlas with its Markdown notes, in Ontario (contract, section 6)', async () => {
    const dataset = await api.sample();
    expect(dataset.file_name).toBe('atlas_sales.xlsx');
    expect(dataset.region).toBe('ON');
    expect(dataset.context).toMatchObject({ name: 'atlas_context.md', format: 'md', converted: false });
    expect(dataset.context?.sections).toHaveLength(10);
  });
});
