import { formatBytes } from '../format';

const MB = 1024 * 1024;

export const SALES_FILE_MAX_BYTES = 20 * MB;
export const CONTEXT_FILE_MAX_BYTES = 5 * MB;

export const SALES_FILE_ACCEPT = '.csv,.xlsx';
export const CONTEXT_FILE_ACCEPT = '.md,.pdf,.docx';

/** A file the browser refuses before sending it. The codes are the contract's. */
export interface FileProblem {
  code: 'unsupported_format' | 'file_too_large';
  message: string;
}

function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot).toLowerCase();
}

export function validateSalesFile(file: File): FileProblem | null {
  const ext = extensionOf(file.name);
  if (ext === '.xls') {
    return {
      code: 'unsupported_format',
      message: `"${file.name}" is an old Excel file (.xls). Save it as .xlsx in Excel, then try again.`,
    };
  }
  if (ext !== '.csv' && ext !== '.xlsx') {
    return {
      code: 'unsupported_format',
      message: `"${file.name}" is not a sales file we can read. Use a CSV or Excel (.xlsx) file.`,
    };
  }
  if (file.size > SALES_FILE_MAX_BYTES) {
    return {
      code: 'file_too_large',
      message: `"${file.name}" is ${formatBytes(file.size)}. The limit is 20 MB.`,
    };
  }
  return null;
}

/** The 50-page limit is checked by the server, which can count pages. */
export function validateContextFile(file: File): FileProblem | null {
  const ext = extensionOf(file.name);
  if (ext === '.doc') {
    return {
      code: 'unsupported_format',
      message: `"${file.name}" is an old Word file (.doc). Save it as .docx in Word, then try again.`,
    };
  }
  if (ext !== '.md' && ext !== '.pdf' && ext !== '.docx') {
    return {
      code: 'unsupported_format',
      message: `"${file.name}" can't be used as a document. Use Markdown (.md), PDF or Word (.docx).`,
    };
  }
  if (file.size > CONTEXT_FILE_MAX_BYTES) {
    return {
      code: 'file_too_large',
      message: `"${file.name}" is ${formatBytes(file.size)}. The limit is 5 MB.`,
    };
  }
  return null;
}

export function contextFormatOf(name: string): 'md' | 'pdf' | 'docx' | null {
  const ext = extensionOf(name);
  if (ext === '.md') return 'md';
  if (ext === '.pdf') return 'pdf';
  if (ext === '.docx') return 'docx';
  return null;
}
