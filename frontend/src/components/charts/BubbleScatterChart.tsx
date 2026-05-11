"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Label,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { CHART_COLORS, CHART_MARGINS, type ChartDataItem } from "./chartTheme";

interface BubbleScatterChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKey: string;
  sizeKey?: string;
  labelKey?: string;
  fixedSize?: number;
  xAxisLabel?: string;
  yAxisLabel?: string;
  yTickFormatter?: (value: number) => string;
  tooltipFormatter?: (payload: ChartDataItem) => React.ReactNode;
  height?: number;
}

// Custom shape that renders a circle + text label above it
function LabeledDot(props: Record<string, unknown>) {
  const { cx, cy, payload, labelKey } = props as {
    cx: number;
    cy: number;
    payload: Record<string, unknown>;
    labelKey?: string;
  };
  const r = (props.r as number) ?? 6;
  const label = labelKey ? String(payload[labelKey] ?? "") : "";

  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill={CHART_COLORS.primary} opacity={0.8} />
      {label && (
        <text
          x={cx}
          y={cy - r - 4}
          textAnchor="middle"
          fill={CHART_COLORS.text}
          fontSize={10}
        >
          {label}
        </text>
      )}
    </g>
  );
}

export default function BubbleScatterChart({
  data,
  xKey,
  yKey,
  sizeKey,
  labelKey,
  fixedSize,
  xAxisLabel,
  yAxisLabel,
  yTickFormatter,
  tooltipFormatter,
  height = 350,
}: BubbleScatterChartProps) {
  const sizeRange: [number, number] = [60, 600];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ ...CHART_MARGINS, top: 30, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
        <XAxis
          type="number"
          dataKey={xKey}
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
        >
          {xAxisLabel && (
            <Label value={xAxisLabel} position="insideBottom" offset={-5} fill={CHART_COLORS.text} fontSize={12} />
          )}
        </XAxis>
        <YAxis
          type="number"
          dataKey={yKey}
          stroke={CHART_COLORS.text}
          tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
          tickFormatter={yTickFormatter}
        >
          {yAxisLabel && (
            <Label value={yAxisLabel} angle={-90} position="insideLeft" fill={CHART_COLORS.text} fontSize={12} />
          )}
        </YAxis>
        {sizeKey && (
          <ZAxis type="number" dataKey={sizeKey} range={sizeRange} />
        )}
        {!sizeKey && fixedSize && (
          <ZAxis type="number" range={[fixedSize, fixedSize]} />
        )}
        <Tooltip
          content={
            <ChartTooltip
              formatter={tooltipFormatter ? (p) => tooltipFormatter(p) : undefined}
            />
          }
        />
        <Scatter
          data={data}
          isAnimationActive={false}
          shape={<LabeledDot labelKey={labelKey} />}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
