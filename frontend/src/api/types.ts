// Types of the API contract, docs/contract.md version 1. The contract is the source of truth:
// change it first, then this file.

export type ProvinceCode =
  | 'ON'
  | 'QC'
  | 'BC'
  | 'AB'
  | 'MB'
  | 'SK'
  | 'NS'
  | 'NB'
  | 'NL'
  | 'PE'
  | 'YT'
  | 'NT'
  | 'NU';

export type CheckStatus = 'ok' | 'warning' | 'error';

export interface Check {
  id: string;
  name: string;
  status: CheckStatus;
  detail: string;
  /** In dollars, or null. */
  amount: number | null;
}

export interface Column {
  name: string;
  /** "text", "date" or "number" in the contract example. */
  type: string;
}

export const ROLE_NAMES = [
  'date',
  'amount',
  'customer',
  'product',
  'quantity',
  'unit_price',
  'region',
  'order_id',
  'target',
] as const;

export type RoleName = (typeof ROLE_NAMES)[number];

/** The column recognized for each role, or null. */
export type Roles = Partial<Record<RoleName, string | null>>;

export type Cell = string | number | boolean | null;

export interface Preview {
  columns: string[];
  rows: Cell[][];
}

export type ContextFormat = 'md' | 'pdf' | 'docx';

/** `full`: whole document in the conversation. `rag`: search. */
export type ContextMode = 'full' | 'rag';

export interface ContextSection {
  id: string;
  title: string;
}

export interface RemovedSection extends ContextSection {
  reason: string;
}

export interface ContextDocument {
  name: string;
  format: ContextFormat;
  converted: boolean;
  /** An estimate. */
  tokens: number;
  mode: ContextMode;
  sections: ContextSection[];
  removed_sections: RemovedSection[];
}

/** Response of POST /api/upload and POST /api/sample. */
export interface Dataset {
  dataset_id: string;
  file_name: string;
  sheets: string[];
  rows: number;
  columns: Column[];
  roles: Roles;
  preview: Preview;
  checks: Check[];
  region: ProvinceCode;
  context: ContextDocument | null;
}

export type ContractErrorCode =
  | 'unsupported_format'
  | 'file_too_large'
  | 'unreadable_file'
  | 'missing_session'
  | 'dataset_not_found'
  | 'rate_limited'
  | 'internal';

/** `network` is frontend only: the server could not be reached. */
export type ErrorCode = ContractErrorCode | 'network';
