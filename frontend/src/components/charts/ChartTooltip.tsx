"use client";

import { CHART_COLORS, type ChartDataItem } from "./chartTheme";

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; color?: string; payload?: ChartDataItem }>;
  label?: string | number;
  formatter?: (payload: ChartDataItem, name?: string) => React.ReactNode;
}

export default function ChartTooltip({ active, payload, label, formatter }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div
      style={{
        background: "#161b22",
        border: `1px solid ${CHART_COLORS.grid}`,
        borderRadius: 6,
        padding: "8px 12px",
        color: CHART_COLORS.text,
        fontSize: 12,
      }}
    >
      {label != null && <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>}
      {payload.map((entry, i) => {
        if (formatter && entry.payload) {
          return <div key={i}>{formatter(entry.payload, entry.name)}</div>;
        }
        return (
          <div key={i} style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </div>
        );
      })}
    </div>
  );
}
