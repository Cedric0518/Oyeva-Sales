import { describe, expect, it } from 'vitest';
import { formatBytes, formatCAD, formatCount, plural } from './format';

describe('formatCAD', () => {
  it('writes dollars with separators, en-CA', () => {
    expect(formatCAD(176.83)).toBe('$176.83');
    expect(formatCAD(649958.8)).toBe('$649,958.80');
  });

  it('puts the minus sign before the dollar sign', () => {
    expect(formatCAD(-13190.44)).toBe('-$13,190.44');
  });
});

describe('formatCount', () => {
  it('adds thousands separators', () => {
    expect(formatCount(59764)).toBe('59,764');
  });
});

describe('formatBytes', () => {
  it('picks a readable unit', () => {
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(12560)).toBe('12.3 KB');
    expect(formatBytes(2913137)).toBe('2.8 MB');
  });
});

describe('plural', () => {
  it('agrees with the count', () => {
    expect(plural(1, 'section')).toBe('1 section');
    expect(plural(10, 'section')).toBe('10 sections');
  });
});
