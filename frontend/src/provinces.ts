import type { ProvinceCode } from './api/types';

/** Fixed list (docs/contract.md, section 4), sorted by name. */
export const PROVINCES: ReadonlyArray<{ code: ProvinceCode; name: string }> = [
  { code: 'AB', name: 'Alberta' },
  { code: 'BC', name: 'British Columbia' },
  { code: 'MB', name: 'Manitoba' },
  { code: 'NB', name: 'New Brunswick' },
  { code: 'NL', name: 'Newfoundland and Labrador' },
  { code: 'NT', name: 'Northwest Territories' },
  { code: 'NS', name: 'Nova Scotia' },
  { code: 'NU', name: 'Nunavut' },
  { code: 'ON', name: 'Ontario' },
  { code: 'PE', name: 'Prince Edward Island' },
  { code: 'QC', name: 'Quebec' },
  { code: 'SK', name: 'Saskatchewan' },
  { code: 'YT', name: 'Yukon' },
];

export const DEFAULT_PROVINCE: ProvinceCode = 'ON';

export function provinceName(code: ProvinceCode): string {
  return PROVINCES.find((p) => p.code === code)?.name ?? code;
}
