import type { ChartSpec, ChartUnit } from '../api/types';
import { formatAxis, formatValue } from '../format';

// The chart spec of the contract (docs/contract.md, section 8) turned into an ECharts option.
// Colors and axes: docs/brand/README.md, section Charts.

export const SERIES_COLORS = ['#9677FF', '#2FC4B2', '#F5A524', '#B6B9C5']; // violet-400, teal-400, amber-400, metal-300
const GRID_LINE = '#262631'; // ink-700
const AXIS_LABEL = '#8E92A0'; // metal-400
const POSITIVE = '#9677FF';
const NEGATIVE = '#F2555A'; // red-400

type Option = Record<string, unknown>;

function valueAxis(unit: ChartUnit): Option {
  return {
    type: 'value',
    axisLabel: { color: AXIS_LABEL, formatter: (v: number) => formatAxis(unit, v) },
    splitLine: { lineStyle: { color: GRID_LINE } },
  };
}

function categoryAxis(values: string[], label: string): Option {
  return {
    type: 'category',
    data: values,
    name: label,
    nameLocation: 'middle',
    nameGap: 28,
    nameTextStyle: { color: AXIS_LABEL },
    axisLabel: { color: AXIS_LABEL },
    axisLine: { lineStyle: { color: GRID_LINE } },
    axisTick: { show: false },
  };
}

function base(spec: ChartSpec): Option {
  return {
    backgroundColor: 'transparent',
    color: SERIES_COLORS,
    textStyle: { fontFamily: 'Inter, system-ui, sans-serif' },
    grid: { left: 16, right: 24, top: spec.series.length > 1 ? 40 : 16, bottom: 40, containLabel: true },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v: number | null) => (v === null || v === undefined ? 'no data' : formatValue(spec.unit, v)),
    },
    legend: spec.series.length > 1 ? { top: 0, textStyle: { color: AXIS_LABEL } } : undefined,
  };
}

/** A waterfall: stacked bars on a transparent base; `measure` gives each bar's role. */
function waterfall(spec: ChartSpec): Option {
  const values = spec.series[0]?.values ?? [];
  const measure = spec.measure ?? values.map((_, i) => (i === 0 ? 'absolute' : 'relative'));
  const baseValues: number[] = [];
  const bars: Array<{ value: number; itemStyle: { color: string } }> = [];
  let running = 0;
  values.forEach((raw, i) => {
    const v = raw ?? 0;
    const role = measure[i] ?? 'relative';
    if (role === 'relative') {
      baseValues.push(v >= 0 ? running : running + v);
      bars.push({ value: Math.abs(v), itemStyle: { color: v >= 0 ? POSITIVE : NEGATIVE } });
      running += v;
    } else {
      if (role === 'absolute') running = v;
      baseValues.push(0);
      bars.push({ value: role === 'total' ? running : v, itemStyle: { color: '#B6B9C5' } });
    }
  });
  return {
    ...base(spec),
    tooltip: { show: false },
    xAxis: categoryAxis(spec.x.values, spec.x.label),
    yAxis: valueAxis(spec.unit),
    series: [
      { name: 'base', type: 'bar', stack: 'waterfall', data: baseValues, itemStyle: { color: 'transparent' }, silent: true },
      { name: spec.series[0]?.name ?? '', type: 'bar', stack: 'waterfall', data: bars, label: { show: true, position: 'top', color: AXIS_LABEL, formatter: (p: { value: number }) => formatAxis(spec.unit, p.value) } },
    ],
  };
}

export function toEChartsOption(spec: ChartSpec): Option {
  if (spec.type === 'waterfall') return waterfall(spec);
  const horizontal = spec.type === 'bar_horizontal';
  const series = spec.series.map((s) => ({
    name: s.name,
    type: spec.type === 'line' || spec.type === 'area' ? 'line' : 'bar',
    data: s.values, // null stays null: a gap, never a zero
    connectNulls: false,
    showSymbol: true,
    symbolSize: 6,
    lineStyle: s.style === 'dashed' ? { type: 'dashed' } : undefined,
    areaStyle: spec.type === 'area' ? { opacity: 0.18 } : undefined,
    barMaxWidth: 36,
  }));
  const categories = categoryAxis(horizontal ? [...spec.x.values].reverse() : spec.x.values, horizontal ? '' : spec.x.label);
  if (horizontal) {
    // Top N reads from the top: the first value goes on the top bar.
    return {
      ...base(spec),
      xAxis: valueAxis(spec.unit),
      yAxis: { ...categories, nameGap: 0 },
      series: series.map((s) => ({ ...s, data: [...s.data].reverse() })),
    };
  }
  return { ...base(spec), xAxis: categories, yAxis: valueAxis(spec.unit), series };
}
