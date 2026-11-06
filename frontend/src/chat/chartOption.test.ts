import { describe, expect, it } from 'vitest';
import type { ChartSpec } from '../api/types';
import { toEChartsOption } from './chartOption';

type Series = { type: string; data: unknown[]; lineStyle?: { type: string }; areaStyle?: object; stack?: string; itemStyle?: { color: string } };
type Axis = { type: string; data?: string[]; axisLabel: { formatter?: (v: number) => string } };

function mapped(spec: ChartSpec) {
  const option = toEChartsOption(spec) as { series: Series[]; xAxis: Axis; yAxis: Axis };
  return option;
}

const MONTHS = { label: 'Month', values: ['2025-01', '2025-02', '2025-03'] };

describe('toEChartsOption', () => {
  it('maps a line, keeps a missing month as a gap and draws a dashed series dashed', () => {
    const option = mapped({
      type: 'line',
      title: 'Sales',
      x: MONTHS,
      series: [
        { name: 'Sales', values: [14972.81, null, 2003.68] },
        { name: 'Target', values: [15000, 15000, 15000], style: 'dashed' },
      ],
      unit: 'CAD',
    });

    expect(option.xAxis).toMatchObject({ type: 'category', data: MONTHS.values });
    expect(option.series[0]).toMatchObject({ type: 'line', data: [14972.81, null, 2003.68], connectNulls: false });
    expect(option.series[0]?.lineStyle).toBeUndefined();
    expect(option.series[1]?.lineStyle).toEqual({ type: 'dashed' });
  });

  it('maps an area as a filled line', () => {
    const option = mapped({ type: 'area', title: 'Sales', x: MONTHS, series: [{ name: 'Sales', values: [1, 2, 3] }], unit: 'CAD' });
    expect(option.series[0]).toMatchObject({ type: 'line' });
    expect(option.series[0]?.areaStyle).toBeDefined();
  });

  it('maps a bar chart on the months', () => {
    const option = mapped({ type: 'bar', title: 'Sales', x: MONTHS, series: [{ name: 'Sales', values: [1, 2, 3] }], unit: 'count' });
    expect(option.xAxis).toMatchObject({ type: 'category', data: MONTHS.values });
    expect(option.yAxis.type).toBe('value');
    expect(option.series[0]).toMatchObject({ type: 'bar', data: [1, 2, 3] });
  });

  it('maps a horizontal bar chart with the first item on top', () => {
    const option = mapped({
      type: 'bar_horizontal',
      title: 'Top categories',
      x: { label: 'Category', values: ['Paper', 'Pens', 'Bags'] },
      series: [{ name: 'Growth', values: [12.4, 8.1, 3.2] }],
      unit: '%',
    });

    expect(option.xAxis.type).toBe('value');
    expect(option.yAxis).toMatchObject({ type: 'category', data: ['Bags', 'Pens', 'Paper'] });
    expect(option.series[0]).toMatchObject({ type: 'bar', data: [3.2, 8.1, 12.4] });
    expect(option.xAxis.axisLabel.formatter?.(12.4)).toBe('12.4%');
  });

  it('maps a waterfall to stacked bars on a transparent base', () => {
    const option = mapped({
      type: 'waterfall',
      title: 'From 2024 to 2025',
      x: { label: 'Step', values: ['2024', 'Stores', 'Online', '2025'] },
      series: [{ name: 'Sales', values: [100, 30, -20, null] }],
      measure: ['absolute', 'relative', 'relative', 'total'],
      unit: 'CAD',
    });

    const [base, bars] = option.series;
    expect(base).toMatchObject({ type: 'bar', stack: 'waterfall', data: [0, 100, 110, 0], itemStyle: { color: 'transparent' } });
    expect(bars?.stack).toBe('waterfall');
    expect((bars?.data as Array<{ value: number }>).map((bar) => bar.value)).toEqual([100, 30, 20, 110]);
  });

  it('writes money on the axis with $ and 1.2M above a million', () => {
    const option = mapped({ type: 'bar', title: 'Sales', x: MONTHS, series: [{ name: 'Sales', values: [1, 2, 3] }], unit: 'CAD' });
    expect(option.yAxis.axisLabel.formatter?.(1_200_000)).toBe('$1.2M');
    expect(option.yAxis.axisLabel.formatter?.(45_000)).toBe('$45,000');
  });
});
