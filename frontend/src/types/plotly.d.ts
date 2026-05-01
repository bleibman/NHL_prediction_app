declare module "react-plotly.js" {
  import { Component } from "react";
  import type { Data, Layout, Config } from "plotly.js";

  interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
    onInitialized?: (figure: { data: Data[]; layout: Partial<Layout> }) => void;
    onUpdate?: (figure: { data: Data[]; layout: Partial<Layout> }) => void;
  }

  export default class Plot extends Component<PlotParams> {}
}

declare namespace Plotly {
  type Data = import("plotly.js").Data;
  type Layout = import("plotly.js").Layout;
  type Config = import("plotly.js").Config;
}
