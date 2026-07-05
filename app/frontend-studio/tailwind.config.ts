import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16202a",
        muted: "#69737d",
        line: "#dbe2ea",
        panel: "#f7f9fb",
        accent: "#0f766e",
        cobalt: "#1d4ed8",
        amber: "#b45309",
        rose: "#be123c",
      },
      boxShadow: {
        soft: "0 18px 40px rgba(22, 32, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
