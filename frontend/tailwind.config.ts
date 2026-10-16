import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        "xs": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "2xs": "0 1px 1px 0 rgba(0, 0, 0, 0.03)",
      },
      backdropBlur: {
        "xs": "2px",
      },
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        navy: {
          900: "#0b132b",
          800: "#1c2541",
          700: "#3a506b",
        },
        accent: {
          teal: "#5bc0be",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};
export default config;
