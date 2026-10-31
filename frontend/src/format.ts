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

/** "1 section", "10 sections". */
export function plural(n: number, one: string, many = `${one}s`): string {
  return `${formatCount(n)} ${n === 1 ? one : many}`;
}
