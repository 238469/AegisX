/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,tsx,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f172a",
        sidebar: "#1e293b",
        primary: "#38bdf8",
        danger: "#f43f5e",
        warning: "#fbbf24",
        success: "#34d399",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [],
}
