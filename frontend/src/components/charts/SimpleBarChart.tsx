"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { CHART_COLORS, CHART_MARGINS, type ChartDataItem } from "./chartTheme";

interface SimpleBarChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKey: string;
  color?: string;
  yAxisLabel?: string;
  height?: number;
  tooltipFormatter?: (payload: ChartDataItem) => React.ReactNode;
}

export default function SimpleBarChart({
  data,
  xKey,
  yKey,
  color = CHART_COLORS.primary,
  yAxisLabel,
  height = 350,
  tooltipFormatter,
}: SimpleBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={CHART_MARGINS}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
        <XAxis
          dataKey={xKey}
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
        />
        <YAxis
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: "insideLeft", fill: CHART_COLORS.text, fontSize: 12 } : undefined}
        />
        <Tooltip
          content={
            <ChartTooltip
              formatter={tooltipFormatter ? (p) => tooltipFormatter(p) : undefined}
            />
          }
        />
        <Bar dataKey={yKey} fill={color} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
