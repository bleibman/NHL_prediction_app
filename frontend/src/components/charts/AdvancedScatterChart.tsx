"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
  Label,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { CHART_COLORS, CHART_MARGINS, interpolateColor, type ChartDataItem } from "./chartTheme";

interface AdvancedScatterChartProps {
  data: ChartDataItem[];
  xKey: string;
  yKey: string;
  colorKey: string;
  sizeKey: string;
  labelKey?: string;
  colorScale?: [string, string, string];
  colorLabel?: string;
  xTickSuffix?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  tooltipFormatter?: (payload: ChartDataItem) => React.ReactNode;
}

function LabeledColorDot(props: Record<string, unknown>) {
  const { cx, cy, fill, payload, labelKey } = props as {
    cx: number;
    cy: number;
    fill: string;
    payload: Record<string, unknown>;
    labelKey?: string;
  };
  const r = (props.r as number) ?? 6;
  const label = labelKey ? String(payload[labelKey] ?? "") : "";

  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill={fill} opacity={0.85} />
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

export default function AdvancedScatterChart({
  data,
  xKey,
  yKey,
  colorKey,
  sizeKey,
  labelKey,
  colorScale = ["#da3633", "#1f6feb", "#58a6ff"],
  colorLabel,
  xTickSuffix,
  xAxisLabel,
  yAxisLabel,
  height = 400,
  tooltipFormatter,
}: AdvancedScatterChartProps) {
  const colorValues = data.map((d) => Number(d[colorKey]) || 0);
  const colorMin = Math.min(...colorValues);
  const colorMax = Math.max(...colorValues);

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ ...CHART_MARGINS, top: 30, right: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            type="number"
            dataKey={xKey}
            stroke={CHART_COLORS.text}
            tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
            tickFormatter={xTickSuffix ? (v) => `${v}${xTickSuffix}` : undefined}
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
          >
            {yAxisLabel && (
              <Label value={yAxisLabel} angle={-90} position="insideLeft" fill={CHART_COLORS.text} fontSize={12} />
            )}
          </YAxis>
          <ZAxis
            type="number"
            dataKey={sizeKey}
            range={[60, 600]}
          />
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
            shape={<LabeledColorDot labelKey={labelKey} />}
          >
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={interpolateColor(Number(d[colorKey]) || 0, colorMin, colorMax, colorScale)}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      {colorLabel && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 4 }}>
          <span style={{ color: CHART_COLORS.text, fontSize: 11 }}>
            {colorMin.toFixed(1)}%
          </span>
          <div
            style={{
              width: 120,
              height: 10,
              borderRadius: 4,
              background: `linear-gradient(to right, ${colorScale[0]}, ${colorScale[1]}, ${colorScale[2]})`,
            }}
          />
          <span style={{ color: CHART_COLORS.text, fontSize: 11 }}>
            {colorMax.toFixed(1)}%
          </span>
          <span style={{ color: CHART_COLORS.muted, fontSize: 11, marginLeft: 4 }}>
            {colorLabel}
          </span>
        </div>
      )}
    </div>
  );
}
