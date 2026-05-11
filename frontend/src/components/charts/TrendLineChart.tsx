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

export interface SeriesConfig {
  key: string;
  name: string;
  color: string;
  dashed?: boolean;
}

interface TrendLineChartProps {
  data: ChartDataItem[];
  xKey: string;
  series: SeriesConfig[];
  reversedX?: boolean;
  showLegend?: boolean;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  tooltipFormatter?: (payload: ChartDataItem, name?: string) => React.ReactNode;
}

export default function TrendLineChart({
  data,
  xKey,
  series,
  reversedX = false,
  showLegend = false,
  xAxisLabel,
  yAxisLabel,
  height = 350,
  tooltipFormatter,
}: TrendLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ ...CHART_MARGINS, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
        <XAxis
          dataKey={xKey}
          reversed={reversedX}
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
        {showLegend && (
          <Legend
            wrapperStyle={{ color: CHART_COLORS.text, fontSize: 12 }}
          />
        )}
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stroke={s.color}
            strokeWidth={s.dashed ? 2 : 2.5}
            strokeDasharray={s.dashed ? "6 3" : undefined}
            dot={{ r: 3, fill: s.color }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
