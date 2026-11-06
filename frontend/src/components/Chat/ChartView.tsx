import { useEffect, useRef } from 'react';
import { BarChart, LineChart } from 'echarts/charts';
import { AriaComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import * as echarts from 'echarts/core';
import { SVGRenderer } from 'echarts/renderers';
import type { ChartSpec } from '../../api/types';
import { toEChartsOption } from '../../chat/chartOption';
import styles from './Results.module.css';

// Only the parts of ECharts the five chart types need, to keep the bundle small.
echarts.use([LineChart, BarChart, GridComponent, LegendComponent, TooltipComponent, AriaComponent, SVGRenderer]);

/** A chart spec of the contract, drawn by ECharts. ECharts also writes a description for screen readers. */
export function ChartView({ spec }: { spec: ChartSpec }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    try {
      // Before the first layout (and in tests) the element has no width yet: start from a default.
      const chart = echarts.init(element, null, {
        renderer: 'svg',
        width: element.clientWidth || 640,
        height: element.clientHeight || 280,
      });
      chart.setOption({ ...toEChartsOption(spec), aria: { enabled: true } });
      const observer =
        typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(() => chart.resize({ width: 'auto', height: 'auto' }));
      observer?.observe(element);
      return () => {
        observer?.disconnect();
        chart.dispose();
      };
    } catch (error) {
      console.warn('The chart could not be drawn.', error);
      return undefined;
    }
  }, [spec]);

  return <div ref={ref} className={styles.chart} />;
}
