"use client";

import dynamic from "next/dynamic";
import { darkLayout } from "./plotlyConfig";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  height?: number;
}

export default function PlotlyChart({ data, layout = {}, height = 350 }: PlotlyChartProps) {
  const mergedLayout: Partial<Plotly.Layout> = {
    ...(darkLayout as Partial<Plotly.Layout>),
    ...layout,
    height,
  };

  return (
    <Plot
      data={data}
      layout={mergedLayout}
      config={{ displayModeBar: false, responsive: true }}
      useResizeHandler
      style={{ width: "100%" }}
    />
  );
}
