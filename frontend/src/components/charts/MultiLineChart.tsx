"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { CHART_COLORS, CHART_MARGINS, type ChartDataItem } from "./chartTheme";

export interface LineConfig {
  key: string;
  name: string;
  color: string;
}

interface MultiLineChartProps {
  data: ChartDataItem[];
  xKey: string;
  lines: LineConfig[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  tooltipFormatter?: (payload: ChartDataItem, name?: string) => React.ReactNode;
}

export default function MultiLineChart({
  data,
  xKey,
  lines,
  xAxisLabel,
  yAxisLabel,
  height = 350,
  tooltipFormatter,
}: MultiLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ ...CHART_MARGINS, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
        <XAxis
          dataKey={xKey}
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5, fill: CHART_COLORS.text, fontSize: 12 } : undefined}
        />
        <YAxis
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: "insideLeft", fill: CHART_COLORS.text, fontSize: 12 } : undefined}
        />
        <Tooltip
          content={
            <ChartTooltip
              formatter={tooltipFormatter ? (p, n) => tooltipFormatter(p, n) : undefined}
            />
          }
        />
        <Legend wrapperStyle={{ color: CHART_COLORS.text, fontSize: 12 }} />
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name}
            stroke={l.color}
            strokeWidth={2}
            dot={{ r: 3, fill: l.color }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
