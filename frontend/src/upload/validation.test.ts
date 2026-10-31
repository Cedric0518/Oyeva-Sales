import { describe, expect, it } from 'vitest';
import { makeFile } from '../test/files';
import { contextFormatOf, validateContextFile, validateSalesFile } from './validation';

const MB = 1024 * 1024;

describe('validateSalesFile', () => {
  it('accepts CSV and XLSX, whatever the case of the extension', () => {
    expect(validateSalesFile(makeFile('atlas_sales.xlsx'))).toBeNull();
    expect(validateSalesFile(makeFile('orders.csv'))).toBeNull();
    expect(validateSalesFile(makeFile('ORDERS.CSV'))).toBeNull();
  });

  it('refuses other formats', () => {
    expect(validateSalesFile(makeFile('notes.pdf'))?.code).toBe('unsupported_format');
    expect(validateSalesFile(makeFile('no_extension'))?.code).toBe('unsupported_format');
  });

  it('explains how to fix an old Excel file', () => {
    expect(validateSalesFile(makeFile('old.xls'))?.message).toContain('Save it as .xlsx');
  });

  it('accepts exactly 20 MB and refuses more', () => {
    expect(validateSalesFile(makeFile('big.csv', 20 * MB))).toBeNull();
    const problem = validateSalesFile(makeFile('big.csv', 20 * MB + 1));
    expect(problem?.code).toBe('file_too_large');
    expect(problem?.message).toBe('"big.csv" is 20 MB. The limit is 20 MB.');
  });
});

describe('validateContextFile', () => {
  it('accepts Markdown, PDF and Word', () => {
    expect(validateContextFile(makeFile('notes.md'))).toBeNull();
    expect(validateContextFile(makeFile('notes.pdf'))).toBeNull();
    expect(validateContextFile(makeFile('notes.DOCX'))).toBeNull();
  });

  it('refuses other formats, with a hint for old Word files', () => {
    expect(validateContextFile(makeFile('notes.txt'))?.code).toBe('unsupported_format');
    expect(validateContextFile(makeFile('notes.doc'))?.message).toContain('Save it as .docx');
  });

  it('refuses more than 5 MB', () => {
    expect(validateContextFile(makeFile('notes.pdf', 5 * MB))).toBeNull();
    expect(validateContextFile(makeFile('notes.pdf', 6 * MB))?.message).toBe('"notes.pdf" is 6 MB. The limit is 5 MB.');
  });
});

describe('contextFormatOf', () => {
  it('maps the extension to the contract format', () => {
    expect(contextFormatOf('a.md')).toBe('md');
    expect(contextFormatOf('a.PDF')).toBe('pdf');
    expect(contextFormatOf('a.docx')).toBe('docx');
    expect(contextFormatOf('a.txt')).toBeNull();
  });
});
