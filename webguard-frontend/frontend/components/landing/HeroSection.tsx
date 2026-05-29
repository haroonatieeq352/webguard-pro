"use client";

import { useState, useEffect } from "react";
import { Shield, Zap, AlertTriangle, CheckCircle, ChevronRight, Globe, Lock } from "lucide-react";

const floatingBadges = [
  { label: "XSS Detected",        color: "text-cyber-red",   bg: "bg-cyber-red/10",   border: "border-cyber-red/30",   icon: AlertTriangle, x: "left-[5%]",   y: "top-[20%]",  delay: "0s"   },
  { label: "SQLi Protected",      color: "text-cyber-green", bg: "bg-cyber-green/10", border: "border-cyber-green/30", icon: CheckCircle,   x: "right-[5%]",  y: "top-[25%]",  delay: "1s"   },
  { label: "SEO Score: 94/100",   color: "text-cyber-cyan",  bg: "bg-cyber-cyan/10",  border: "border-cyber-cyan/30",  icon: Zap,           x: "left-[3%]",   y: "bottom-[30%]", delay: "2s" },
  { label: "HTTPS Enforced ✓",    color: "text-cyber-green", bg: "bg-cyber-green/10", border: "border-cyber-green/30", icon: Lock,          x: "right-[4%]",  y: "bottom-[25%]", delay: "0.5s" },
];

const scanExamples = [
  "https://yourwebsite.com",
  "https://myshop.pk",
  "https://mybusiness.io",
  "https://example.com",
];

const stats = [
  { value: "50K+",   label: "Scans Run",           color: "text-cyber-cyan"  },
  { value: "12K+",   label: "Vulnerabilities Found", color: "text-cyber-red"  },
  { value: "98%",    label: "Detection Accuracy",    color: "text-cyber-green" },
  { value: "< 60s",  label: "Average Scan Time",     color: "text-cyber-cyan"  },
];

export default function HeroSection() {
  const [url,         setUrl]         = useState("");
  const [placeholder, setPlaceholder] = useState(scanExamples[0]);
  const [isScanning,  setIsScanning]  = useState(false);
  const [errorMsg,    setErrorMsg]    = useState("");
  const [exampleIdx,  setExampleIdx]  = useState(0);

  // Rotate placeholder text
  useEffect(() => {
    const interval = setInterval(() => {
      setExampleIdx((i) => {
        const next = (i + 1) % scanExamples.length;
        setPlaceholder(scanExamples[next]);
        return next;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  function validateUrl(input: string): boolean {
    try {
      const parsed = new URL(input);
      return ["http:", "https:"].includes(parsed.protocol);
    } catch {
      return false;
    }
  }

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg("");
    if (!url.trim()) {
      setErrorMsg("Please enter a website URL to scan.");
      return;
    }
    const toScan = url.startsWith("http") ? url : `https://${url}`;
    if (!validateUrl(toScan)) {
      setErrorMsg("Please enter a valid URL (e.g. https://yoursite.com)");
      return;
    }
    setIsScanning(true);
    // TODO: Connect to Django API — POST /api/scans/
    await new Promise((r) => setTimeout(r, 2000)); // simulate
    setIsScanning(false);
    window.location.href = `/auth/register?scan=${encodeURIComponent(toScan)}`;
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">

      {/* ── Background layers ─────────────────────────────── */}
      <div className="absolute inset-0 bg-hero-grad" />
      <div className="absolute inset-0 cyber-grid-bg opacity-60" />

      {/* Radial glow center */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-cyber-cyan/5 blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] rounded-full bg-purple-500/5 blur-[80px] pointer-events-none" />

      {/* Floating badges — desktop only */}
      {floatingBadges.map((badge) => {
        const Icon = badge.icon;
        return (
          <div
            key={badge.label}
            className={`hidden xl:flex absolute items-center gap-2 px-3 py-2 rounded-lg border ${badge.bg} ${badge.border} animate-float`}
            style={{ [badge.x.startsWith("left") ? "left" : "right"]: badge.x.replace("left-[", "").replace("right-[", "").replace("]", ""), [badge.y.startsWith("top") ? "top" : "bottom"]: badge.y.replace("top-[", "").replace("bottom-[", "").replace("]", ""), animationDelay: badge.delay }}
          >
            <Icon className={`w-3.5 h-3.5 ${badge.color}`} />
            <span className={`text-xs font-semibold ${badge.color}`}>{badge.label}</span>
          </div>
        );
      })}

      {/* ── Main Content ──────────────────────────────────── */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyber-cyan/30 bg-cyber-cyan/5 mb-8 animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-cyber-green animate-ping-slow" />
          <span className="text-xs font-semibold text-cyber-cyan tracking-wide uppercase">
            OWASP Top 10 · 2025 Standards · AI-Powered
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black mb-6 animate-fade-in-up leading-tight">
          <span className="gradient-text-white">Is Your Website</span>
          <br />
          <span className="gradient-text-cyan">Truly Secure?</span>
        </h1>

        {/* Subheadline */}
        <p className="text-lg sm:text-xl text-cyber-muted max-w-3xl mx-auto mb-10 animate-fade-in-up leading-relaxed" style={{ animationDelay: "0.1s" }}>
          Scan for <span className="text-white font-semibold">OWASP Top 10 vulnerabilities</span>,
          SEO issues &amp; performance problems in seconds.
          Get an <span className="text-cyber-cyan font-semibold">AI-powered security report</span> with
          actionable fixes — at a fraction of enterprise tool costs.
        </p>

        {/* ── Scan Input ─────────────────────────────────── */}
        <form
          onSubmit={handleScan}
          className="max-w-2xl mx-auto mb-4 animate-fade-in-up"
          style={{ animationDelay: "0.2s" }}
        >
          <div className="flex flex-col sm:flex-row gap-3 p-2 bg-cyber-card/80 backdrop-blur-md border border-cyber-border rounded-2xl shadow-cyber">
            <div className="flex-1 flex items-center gap-3 px-4">
              <Globe className="w-5 h-5 text-cyber-muted flex-shrink-0" />
              <input
                type="text"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setErrorMsg(""); }}
                placeholder={placeholder}
                className="w-full bg-transparent text-cyber-text placeholder:text-cyber-muted/60 text-sm sm:text-base focus:outline-none py-3"
                aria-label="Website URL to scan"
                autoComplete="off"
                spellCheck={false}
              />
            </div>
            <button
              type="submit"
              disabled={isScanning}
              className="btn-cyber flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold rounded-xl whitespace-nowrap flex-shrink-0 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isScanning ? (
                <>
                  <div className="w-4 h-4 border-2 border-cyber-bg border-t-transparent rounded-full animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Free Scan
                </>
              )}
            </button>
          </div>
          {errorMsg && (
            <p className="mt-2 text-sm text-cyber-red text-left px-2">{errorMsg}</p>
          )}
        </form>

        {/* Trust note */}
        <p className="text-xs text-cyber-muted mb-12 animate-fade-in" style={{ animationDelay: "0.3s" }}>
          ✓ No credit card required &nbsp;·&nbsp; ✓ 3 free scans/month &nbsp;·&nbsp; ✓ Results in under 60 seconds
        </p>

        {/* ── Stats Row ──────────────────────────────────── */}
        <div
          className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mx-auto animate-fade-in-up"
          style={{ animationDelay: "0.4s" }}
        >
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="cyber-card p-4 text-center rounded-xl"
            >
              <div className={`text-2xl sm:text-3xl font-black ticker ${stat.color}`}>
                {stat.value}
              </div>
              <div className="text-xs text-cyber-muted mt-1 leading-tight">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Scroll hint */}
        <div className="mt-16 flex flex-col items-center gap-2 animate-fade-in" style={{ animationDelay: "0.6s" }}>
          <span className="text-xs text-cyber-muted">Scroll to explore</span>
          <div className="w-5 h-8 border border-cyber-border rounded-full flex items-start justify-center p-1">
            <div className="w-1.5 h-2 rounded-full bg-cyber-cyan animate-bounce" />
          </div>
        </div>
      </div>
    </section>
  );
}
