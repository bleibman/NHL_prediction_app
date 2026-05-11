"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  LabelList,
  ResponsiveContainer,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { CHART_COLORS, CHART_MARGINS, interpolateColor, type ChartDataItem } from "./chartTheme";

interface HorizontalBarChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKey: string;
  colorScale?: [string, string, string];
  labelFormatter?: (value: unknown) => string;
  tooltipFormatter?: (payload: ChartDataItem) => React.ReactNode;
  xAxisLabel?: string;
  height?: number;
}

export default function HorizontalBarChart({
  data,
  xKey,
  yKey,
  colorScale,
  labelFormatter,
  tooltipFormatter,
  xAxisLabel,
  height = 400,
}: HorizontalBarChartProps) {
  const values = data.map((d) => Number(d[xKey]) || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ ...CHART_MARGINS, left: 60, right: 80 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} horizontal={false} />
        <XAxis
          type="number"
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5, fill: CHART_COLORS.text, fontSize: 12 } : undefined}
        />
        <YAxis
          type="category"
          dataKey={yKey}
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          width={55}
        />
        <Tooltip
          content={
            <ChartTooltip
              formatter={tooltipFormatter ? (p) => tooltipFormatter(p) : undefined}
            />
          }
        />
        <Bar dataKey={xKey} isAnimationActive={false}>
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={
                colorScale
                  ? interpolateColor(Number(d[xKey]) || 0, min, max, colorScale)
                  : CHART_COLORS.primary
              }
            />
          ))}
          <LabelList
            dataKey={xKey}
            position="right"
            fill={CHART_COLORS.text}
            fontSize={12}
            formatter={labelFormatter ?? ((v: unknown) => String(v))}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
