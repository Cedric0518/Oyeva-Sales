import type { Check, CheckStatus, ContextFormat, ContextMode, RoleName } from '../../api/types';
import { plural } from '../../format';

export const STATUS_LABEL: Record<CheckStatus, string> = {
  ok: 'OK',
  warning: 'Warning',
  error: 'Error',
};

/** "1 error, 6 warnings, 1 OK": the counts in words, worst first. */
export function summarizeChecks(checks: Check[]): string {
  if (checks.length === 0) return 'No checks';
  const count = (status: CheckStatus) => checks.filter((c) => c.status === status).length;
  return [
    count('error') > 0 && plural(count('error'), 'error'),
    count('warning') > 0 && plural(count('warning'), 'warning'),
    count('ok') > 0 && `${count('ok')} OK`,
  ]
    .filter(Boolean)
    .join(', ');
}

export const ROLE_LABEL: Record<RoleName, string> = {
  date: 'Date',
  amount: 'Amount',
  customer: 'Customer',
  product: 'Product',
  quantity: 'Quantity',
  unit_price: 'Unit price',
  region: 'Store or region',
  order_id: 'Order number',
  target: 'Target',
};

export const FORMAT_LABEL: Record<ContextFormat, string> = {
  md: 'Markdown',
  pdf: 'PDF',
  docx: 'Word',
};

export const MODE_LABEL: Record<ContextMode, { name: string; explanation: string }> = {
  full: { name: 'Whole document', explanation: 'The assistant reads all of it for every question.' },
  rag: { name: 'Search', explanation: 'The document is long: the assistant searches it for each question.' },
};
