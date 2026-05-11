// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ChartDataItem = any;

export const CHART_COLORS = {
  bg: "transparent",
  grid: "#21262d",
  text: "#c9d1d9",
  primary: "#1f6feb",
  primaryLight: "#58a6ff",
  muted: "#484f58",
} as const;

export const TEAM_COLORS = [
  "#1f6feb", "#58a6ff", "#f78166", "#7ee787", "#d2a8ff",
  "#ff7b72", "#79c0ff", "#ffa657", "#56d4dd", "#e6edf3",
  "#b392f0", "#ffdf5d", "#85e89d", "#f692ce", "#9ecbff",
  "#dbedff",
];

export const CHART_MARGINS = { top: 20, right: 30, bottom: 20, left: 40 };

export function interpolateColor(
  value: number,
  min: number,
  max: number,
  colors: [string, string, string] = ["#21262d", "#1f6feb", "#58a6ff"]
): string {
  const t = max === min ? 0.5 : (value - min) / (max - min);
  const [low, mid, high] = colors;
  if (t <= 0.5) {
    return lerpHex(low, mid, t * 2);
  }
  return lerpHex(mid, high, (t - 0.5) * 2);
}

function lerpHex(a: string, b: string, t: number): string {
  const parse = (hex: string) => {
    const h = hex.replace("#", "");
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  };
  const [r1, g1, b1] = parse(a);
  const [r2, g2, b2] = parse(b);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const bl = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${bl.toString(16).padStart(2, "0")}`;
}
