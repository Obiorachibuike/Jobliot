/** @type {import('tailwindcss').Config} */

// Semantic color names map to CSS variables defined in
// src/theme/index.css.  Switching themes toggles the `dark`
// class on <html>, which swaps the variable values instantly.
const withAlpha = (name) => `rgb(var(${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // backgrounds
        "bg-main": withAlpha("--bg-main"),
        "bg-sidebar": withAlpha("--bg-sidebar"),
        "bg-surface": withAlpha("--bg-surface"),
        "bg-elevated": withAlpha("--bg-elevated"),
        "bg-secondary": withAlpha("--bg-secondary"),
        "bg-input": withAlpha("--input-bg"),
        // text
        "text-primary": withAlpha("--text-primary"),
        "text-secondary": withAlpha("--text-secondary"),
        "text-muted": withAlpha("--text-muted"),
        // brand + semantic
        accent: withAlpha("--accent"),
        "accent-hover": withAlpha("--accent-hover"),
        brand: withAlpha("--accent"),
        brandhover: withAlpha("--accent-hover"),
        success: withAlpha("--success"),
        warning: withAlpha("--warning"),
        danger: withAlpha("--error"),
        border: withAlpha("--border"),
        input: withAlpha("--input-bg"),
        surface: withAlpha("--bg-surface"),
        elevated: withAlpha("--bg-elevated"),
        secondary: withAlpha("--bg-secondary"),
        primary: withAlpha("--text-primary"),
        muted: withAlpha("--text-muted"),
        // literal brand neon (for decorative glows only)
        neon: "#39FF14",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        glow: "0 0 12px rgba(57, 255, 20, 0.25)",
        soft: "0 1px 2px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.06)",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
