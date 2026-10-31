/** Joins the class names that are set: cx('a', false, 'b') -> "a b". */
export function cx(...names: Array<string | false | null | undefined>): string {
  return names.filter(Boolean).join(' ');
}
