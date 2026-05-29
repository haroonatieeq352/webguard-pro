/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Dark Cyber Shield Theme ──────────────────────
        cyber: {
          bg:        "#0A0E1A",   // deep navy-black
          card:      "#111827",   // card background
          border:    "#1E2A3A",   // subtle borders
          cyan:      "#00D4FF",   // primary electric cyan
          "cyan-dim":"#0099BB",   // dimmed cyan
          red:       "#FF4757",   // danger / vulnerability
          green:     "#2ED573",   // success / passed
          orange:    "#FF6B35",   // warning / medium risk
          purple:    "#A78BFA",   // info / accent
          text:      "#E2E8F0",   // primary text
          muted:     "#94A3B8",   // muted text
          dark:      "#060912",   // deepest bg
        },
        // ── Severity Colors ───────────────────────────────
        severity: {
          critical: "#FF1744",
          high:     "#FF4757",
          medium:   "#FF6B35",
          low:      "#FFD60A",
          info:     "#00D4FF",
          pass:     "#2ED573",
        },
      },
      fontFamily: {
        sans:  ["var(--font-inter)", "system-ui", "sans-serif"],
        mono:  ["var(--font-fira-code)", "JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "cyber-grid": "linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)",
        "cyber-glow":  "radial-gradient(ellipse at center, rgba(0,212,255,0.15) 0%, transparent 70%)",
        "hero-grad":   "linear-gradient(135deg, #060912 0%, #0A0E1A 40%, #0D1B2A 100%)",
        "card-grad":   "linear-gradient(135deg, #111827 0%, #0D1521 100%)",
        "cyan-grad":   "linear-gradient(135deg, #00D4FF 0%, #0099BB 100%)",
        "danger-grad": "linear-gradient(135deg, #FF4757 0%, #C0392B 100%)",
        "green-grad":  "linear-gradient(135deg, #2ED573 0%, #1E9E52 100%)",
      },
      backgroundSize: {
        "grid-sm": "30px 30px",
        "grid-md": "50px 50px",
      },
      boxShadow: {
        "cyber":       "0 0 20px rgba(0,212,255,0.15), 0 4px 24px rgba(0,0,0,0.4)",
        "cyber-hover": "0 0 40px rgba(0,212,255,0.25), 0 8px 32px rgba(0,0,0,0.5)",
        "cyber-lg":    "0 0 60px rgba(0,212,255,0.20), 0 20px 60px rgba(0,0,0,0.6)",
        "danger":      "0 0 20px rgba(255,71,87,0.20), 0 4px 20px rgba(0,0,0,0.4)",
        "green":       "0 0 20px rgba(46,213,115,0.20), 0 4px 20px rgba(0,0,0,0.4)",
        "card":        "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
      },
      animation: {
        "glow-pulse":   "glowPulse 3s ease-in-out infinite",
        "scan-line":    "scanLine 2s linear infinite",
        "float":        "float 6s ease-in-out infinite",
        "fade-in-up":   "fadeInUp 0.6s ease-out",
        "fade-in":      "fadeIn 0.5s ease-out",
        "spin-slow":    "spin 8s linear infinite",
        "ping-slow":    "ping 3s cubic-bezier(0,0,0.2,1) infinite",
        "matrix":       "matrix 20s linear infinite",
        "border-glow":  "borderGlow 2s ease-in-out infinite",
        "number-count": "numberCount 2s ease-out",
      },
      keyframes: {
        glowPulse: {
          "0%, 100%": { opacity: "0.4", transform: "scale(1)" },
          "50%":      { opacity: "0.8", transform: "scale(1.05)" },
        },
        scanLine: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-20px)" },
        },
        fadeInUp: {
          "0%":   { opacity: "0", transform: "translateY(30px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        matrix: {
          "0%":   { backgroundPosition: "0% 0%" },
          "100%": { backgroundPosition: "0% 100%" },
        },
        borderGlow: {
          "0%, 100%": { borderColor: "rgba(0,212,255,0.3)" },
          "50%":      { borderColor: "rgba(0,212,255,0.8)" },
        },
        numberCount: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      borderRadius: {
        "cyber": "0.375rem",
      },
    },
  },
  plugins: [],
};
