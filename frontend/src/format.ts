const cad = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });
const count = new Intl.NumberFormat('en-CA');
const oneDecimal = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 1 });

/** Dollars with separators: 176.83 -> "$176.83", -13190.44 -> "-$13,190.44". */
export function formatCAD(value: number): string {
  return cad.format(value);
}

/** 59764 -> "59,764". */
export function formatCount(value: number): string {
  return count.format(value);
}

/** File sizes, base 1024: 20971520 -> "20 MB". */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${oneDecimal.format(bytes / 1024)} KB`;
  return `${oneDecimal.format(bytes / (1024 * 1024))} MB`;
}

// ---------- Chart and table values (frontend/CLAUDE.md, section 6) ----------

const cadWhole = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat('en-CA', { notation: 'compact', maximumFractionDigits: 1 });
const upToTwo = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 2 });

type Unit = 'CAD' | '%' | 'count' | 'days';

/**
 * A value in its unit, for tooltips and text. `%` values are percent numbers: 5.06 -> "5.1%".
 */
export function formatValue(unit: Unit, value: number): string {
  switch (unit) {
    case 'CAD':
      return formatCAD(value);
    case '%':
      return `${oneDecimal.format(value)}%`;
    case 'count':
      return upToTwo.format(value);
    case 'days':
      return `${oneDecimal.format(value)} ${Math.abs(value) === 1 ? 'day' : 'days'}`;
  }
}

/** A value on an axis: short, and `1.2M` above a million. 1250000 CAD -> "$1.2M". */
export function formatAxis(unit: Unit, value: number): string {
  const big = Math.abs(value) >= 1_000_000;
  const sign = value < 0 ? '-' : '';
  switch (unit) {
    case 'CAD':
      return big ? `${sign}$${compact.format(Math.abs(value))}` : cadWhole.format(value);
    case '%':
      return `${oneDecimal.format(value)}%`;
    case 'count':
      return big ? compact.format(value) : upToTwo.format(value);
    case 'days':
      return oneDecimal.format(value);
  }
}

/** A number in a table cell, which has no unit: 649958.8 -> "649,958.8". */
export function formatNumber(value: number): string {
  return upToTwo.format(value);
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-08" -> "August 2026". Anything else stays as it is. */
export function formatMonth(value: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(value);
  const name = match ? MONTHS[Number(match[2]) - 1] : undefined;
  return match && name ? `${name} ${match[1]}` : value;
}

/** "1 section", "10 sections". */
export function plural(n: number, one: string, many = `${one}s`): string {
  return `${formatCount(n)} ${n === 1 ? one : many}`;
}
