import { describe, expect, it } from 'vitest';
import { formatAxis, formatBytes, formatCAD, formatCount, formatMonth, formatNumber, formatValue, plural } from './format';

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

describe('chart values', () => {
  it('writes each unit in words people read', () => {
    expect(formatValue('CAD', 2003.68)).toBe('$2,003.68');
    expect(formatValue('%', 5.06)).toBe('5.1%');
    expect(formatValue('count', 805)).toBe('805');
    expect(formatValue('days', 1)).toBe('1 day');
    expect(formatValue('days', 12.5)).toBe('12.5 days');
  });

  it('keeps axis labels short, 1.2M above a million', () => {
    expect(formatAxis('CAD', 1_200_000)).toBe('$1.2M');
    expect(formatAxis('CAD', -2_500_000)).toBe('-$2.5M');
    expect(formatAxis('CAD', 60_000)).toBe('$60,000');
    expect(formatAxis('count', 3_400_000)).toBe('3.4M');
  });

  it('writes table numbers with separators and a published month in words', () => {
    expect(formatNumber(649958.8)).toBe('649,958.8');
    expect(formatMonth('2026-08')).toBe('August 2026');
    expect(formatMonth('2026-10-12')).toBe('2026-10-12');
  });
});
