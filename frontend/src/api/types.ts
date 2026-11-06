// Types of the API contract, docs/contract.md version 3. The contract is the source of truth:
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
  | 'invalid_request'
  | 'missing_session'
  | 'dataset_not_found'
  | 'rate_limited'
  | 'internal';

/** `network` is frontend only: the server could not be reached. */
export type ErrorCode = ContractErrorCode | 'network';

// ---------- Chat: POST /api/chat, Server-Sent Events (docs/contract.md, sections 2, 7 and 8) ----------

export interface ChatRequest {
  dataset_id: string;
  /** null on the first message, then the one received in the latest `start` event. */
  conversation_id: string | null;
  message: string;
}

export type Provenance = 'certified' | 'exploratory' | 'market' | 'documents' | 'context';

export interface Metric {
  name: string;
  version: number;
  definition?: string;
}

export type ChartType = 'line' | 'bar' | 'bar_horizontal' | 'area' | 'waterfall';
export type ChartUnit = 'CAD' | '%' | 'count' | 'days';
export type WaterfallMeasure = 'absolute' | 'relative' | 'total';

export interface ChartSeries {
  name: string;
  /** null: no row in the file for that point. Drawn as a gap, never a zero. */
  values: Array<number | null>;
  style?: 'dashed';
}

export interface ChartSpec {
  type: ChartType;
  title: string;
  x: { label: string; values: string[] };
  series: ChartSeries[];
  unit: ChartUnit;
  /** waterfall only: the role of each bar. */
  measure?: WaterfallMeasure[];
}

/** Fields that tell how a chart or a table was made: `metric` for certified, the benchmark for market. */
export interface Origin {
  metric?: Metric;
  benchmark?: string;
  source?: string;
  published?: string;
}

export type StepTool = 'certified' | 'code' | 'market' | 'documents' | 'web';
export type StepStatus = 'running' | 'done' | 'failed';

export interface StepEvent {
  id: string;
  tool: StepTool;
  label: string;
  status: StepStatus;
  metric?: Metric;
  code?: string;
}

export interface ChartEvent extends Origin {
  id: string;
  provenance: Provenance;
  chart: ChartSpec;
}

export interface TableEvent extends Origin {
  id: string;
  provenance: Provenance;
  title: string;
  columns: string[];
  rows: Cell[][];
}

export interface Citation {
  id: string;
  doc: string;
  section: string;
  excerpt: string;
  /** null in `full` mode, the reranker score in `rag` mode. */
  score: number | null;
}

export interface WebSource {
  id: string;
  title: string;
  url: string;
  published?: string;
}

export type ChatEvent =
  | { type: 'start'; data: { conversation_id: string | null; message_id: string } }
  | { type: 'step'; data: StepEvent }
  | { type: 'text'; data: { delta: string } }
  | { type: 'chart'; data: ChartEvent }
  | { type: 'table'; data: TableEvent }
  | { type: 'citations'; data: { covered: boolean; items: Citation[] } }
  | { type: 'sources'; data: { items: WebSource[] } }
  | { type: 'blocked'; data: { message: string } }
  | { type: 'error'; data: { code: string; message: string } }
  | { type: 'done'; data: Record<string, never> };

export type ChatEventType = ChatEvent['type'];
