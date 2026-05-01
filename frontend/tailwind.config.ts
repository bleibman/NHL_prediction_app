import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0d1117",
          card: "#161b22",
          gradient: "#1c2333",
        },
        border: "#21262d",
        text: {
          DEFAULT: "#c9d1d9",
          bright: "#f0f6fc",
          muted: "#8b949e",
        },
        primary: {
          DEFAULT: "#1f6feb",
          hover: "#388bfd",
          light: "#58a6ff",
        },
        accent: {
          green: "#3fb950",
          orange: "#d29922",
          red: "#f85149",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
