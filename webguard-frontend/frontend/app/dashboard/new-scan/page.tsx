"use client";

import { useState, useEffect } from "react";
import {
  ScanSearch, Globe, Shield, TrendingUp, Zap,
  AlertTriangle, CheckCircle2, Loader2, Info, XCircle,
} from "lucide-react";
import { apiPost, apiGet } from "../../../lib/api";

const scanTypes = [
  {
    id: "quick",
    label: "Quick Scan",
    desc: "Security headers + basic SEO. ~30 seconds.",
    icon: Zap,
    color: "#2ED573",
    time: "~30s",
    tier: "Free",
  },
  {
    id: "standard",
    label: "Standard Scan",
    desc: "Full SEO audit + performance + code quality.",
    icon: ScanSearch,
    color: "#00D4FF",
    time: "~2 min",
    tier: "Free",
  },
  {
    id: "deep",
    label: "Deep DAST Scan",
    desc: "OWASP Top 10 active testing via ZAP engine.",
    icon: Shield,
    color: "#FF6B35",
    time: "~10 min",
    tier: "Pro",
  },
  {
    id: "full",
    label: "Full Audit",
    desc: "All checks: DAST + business logic + subdomains.",
    icon: AlertTriangle,
    color: "#A78BFA",
    time: "~20 min",
    tier: "Business",
  },
];

const modules = [
  { id: "security_headers", label: "Security Headers", desc: "CSP, HSTS, X-Frame-Options…", default: true },
  { id: "seo",              label: "SEO Audit",        desc: "Meta, H1, OG tags, sitemap",  default: true },
  { id: "performance",      label: "Performance",      desc: "PageSpeed Insights API",       default: true },
  { id: "code_quality",     label: "Code Quality",     desc: "JS minify, inline CSS, SRI",   default: false },
  { id: "ssl_tls",          label: "SSL/TLS Analysis", desc: "Cipher strength, cert validity", default: false },
  { id: "owasp",            label: "OWASP Top 10",     desc: "SQLi, XSS, CSRF checks",       default: false, pro: true },
];

type ScanStatus = "idle" | "scanning" | "done" | "error";

export default function NewScanPage() {
  const [url, setUrl]             = useState("");
  const [scanType, setScanType]   = useState("standard");
  const [selectedModules, setSelectedModules] = useState<string[]>(
    modules.filter((m) => m.default).map((m) => m.id)
  );
  const [status, setStatus]       = useState<ScanStatus>("idle");
  const [progress, setProgress]   = useState(0);
  const [urlError, setUrlError]   = useState("");
  const [createdScanId, setCreatedScanId] = useState<string | null>(null);
  const [apiError, setApiError]   = useState("");

  function toggleModule(id: string) {
    setSelectedModules((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  }

  function validateUrl(value: string): boolean {
    setUrlError("");
    if (!value.trim()) { setUrlError("Please enter a URL to scan."); return false; }
    try {
      const u = new URL(value.startsWith("http") ? value : `https://${value}`);
      if (!u.hostname.includes(".")) { setUrlError("Enter a valid domain name."); return false; }
      const privateRanges = /^(localhost|127\.|192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/;
      if (privateRanges.test(u.hostname)) { setUrlError("Private/local IPs cannot be scanned."); return false; }
      return true;
    } catch {
      setUrlError("Enter a valid URL (e.g. https://example.com).");
      return false;
    }
  }

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");
    setUrlError("");
    const cleaned = url.trim().startsWith("http") ? url.trim() : `https://${url.trim()}`;
    if (!validateUrl(cleaned)) return;

    setStatus("scanning");
    setProgress(0);

    const backendScanType = scanType === "standard" ? "quick" : scanType;

    try {
      const response = await apiPost("scans/new/", {
        url: cleaned,
        scan_type: backendScanType,
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.message || data.error || data.detail || "Failed to start scan request.";
        setApiError(errorMsg);
        setStatus("error");
        return;
      }

      const scanId = data.id;
      setCreatedScanId(scanId);

      // Start status checking loop
      let isChecking = true;
      let currentProgress = 0;
      const progressIncrement = scanType === "quick" || scanType === "standard" ? 6 : 1;
      const maxSimulatedProgress = scanType === "quick" || scanType === "standard" ? 92 : 96;

      const progressInterval = setInterval(() => {
        currentProgress = Math.min(currentProgress + progressIncrement, maxSimulatedProgress);
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return Math.max(prev, currentProgress);
        });
      }, 600);

      const checkStatus = async () => {
        if (!isChecking) return;
        try {
          const res = await apiGet(`scans/results/${scanId}/`);
          if (res.ok) {
            const resultData = await res.json();
            const scanStatus = resultData.scan.status;

            if (scanStatus === "completed") {
              isChecking = false;
              clearInterval(progressInterval);
              setProgress(100);
              setStatus("done");
            } else if (scanStatus === "failed") {
              isChecking = false;
              clearInterval(progressInterval);
              setApiError("Backend scan engine failed to process the website. Check that the target is online and accessible.");
              setStatus("error");
            }
          }
        } catch (pollErr) {
          // Ignore network errors and retry
        }

        if (isChecking) {
          setTimeout(checkStatus, 3000);
        }
      };

      // Trigger initial status check
      setTimeout(checkStatus, 1500);

    } catch (err) {
      setApiError("Could not connect to the scan server. Make sure the backend is running.");
      setStatus("error");
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-cyber-text">Start a New Scan</h2>
        <p className="text-sm text-cyber-muted mt-1">
          Enter a URL and configure your scan settings below.
        </p>
      </div>

      {/* ── Scanning progress overlay ────────────────────── */}
      {status === "scanning" && (
        <div className="cyber-card p-6 border border-cyber-cyan/30 text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-cyber-cyan/10 rounded-full border border-cyber-cyan/20 flex items-center justify-center scan-line-anim">
            <Loader2 className="w-8 h-8 text-cyber-cyan animate-spin" />
          </div>
          <div>
            <p className="font-semibold text-cyber-text mb-1">Scanning {url}...</p>
            <p className="text-xs text-cyber-muted">Running {selectedModules.length} modules</p>
          </div>
          <div className="w-full bg-cyber-border rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: "linear-gradient(90deg, #00D4FF, #A78BFA)",
                boxShadow: "0 0 12px rgba(0,212,255,0.4)",
              }}
            />
          </div>
          <p className="text-sm font-bold text-cyber-cyan">{progress}%</p>
        </div>
      )}

      {/* ── Scan done ──────────────────────────────────────── */}
      {status === "done" && (
        <div className="cyber-card p-6 border border-cyber-green/30 flex items-center gap-4">
          <div className="w-12 h-12 bg-cyber-green/10 rounded-full border border-cyber-green/30 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-6 h-6 text-cyber-green" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-cyber-text">Scan Complete!</p>
            <p className="text-xs text-cyber-muted">Results are ready to view.</p>
          </div>
          <a
            href={`/dashboard/results?id=${createdScanId}`}
            className="btn-cyber px-4 py-2 text-sm font-bold inline-flex items-center gap-2"
          >
            View Results
          </a>
        </div>
      )}

      {/* ── Scan form ──────────────────────────────────────── */}
      {(status === "idle" || status === "error") && (
        <form onSubmit={handleScan} className="space-y-6">
          {/* API Error Banner */}
          {apiError && (
            <div className="mb-5 p-3.5 bg-cyber-red/10 border border-cyber-red/30 rounded-lg flex items-start gap-3 animate-fade-in">
              <AlertTriangle className="w-4.5 h-4.5 text-cyber-red mt-0.5 flex-shrink-0" />
              <p className="text-sm text-cyber-red">{apiError}</p>
            </div>
          )}
          {/* URL input */}
          <div className="cyber-card p-6 space-y-3">
            <label htmlFor="scan-url" className="block text-sm font-semibold text-cyber-text">
              Target URL
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cyber-muted" />
              <input
                id="scan-url"
                type="text"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setUrlError(""); }}
                placeholder="https://example.com"
                className={`scan-input w-full pl-11 pr-4 py-3.5 text-sm ${
                  urlError ? "border-cyber-red/60" : ""
                }`}
                autoFocus
              />
            </div>
            {urlError && (
              <p className="text-xs text-cyber-red flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                {urlError}
              </p>
            )}
            <p className="text-xs text-cyber-muted flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 flex-shrink-0" />
              Private IPs and localhost are blocked for security.
            </p>
          </div>

          {/* Scan type */}
          <div className="cyber-card p-6 space-y-4">
            <h3 className="text-sm font-semibold text-cyber-text">Scan Type</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {scanTypes.map((type) => {
                const Icon = type.icon;
                const selected = scanType === type.id;
                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setScanType(type.id)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      selected
                        ? "border-cyber-cyan/50 bg-cyber-cyan/5"
                        : "border-cyber-border hover:border-cyber-cyan/30 hover:bg-cyber-cyan/5"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ background: `${type.color}15`, border: `1px solid ${type.color}30` }}
                      >
                        <Icon className="w-4 h-4" style={{ color: type.color }} />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-cyber-muted">{type.time}</span>
                        <span
                          className="badge"
                          style={{
                            background: type.tier === "Free" ? "#2ED57315" : type.tier === "Pro" ? "#00D4FF15" : "#A78BFA15",
                            color: type.tier === "Free" ? "#2ED573" : type.tier === "Pro" ? "#00D4FF" : "#A78BFA",
                            border: `1px solid ${type.tier === "Free" ? "#2ED57330" : type.tier === "Pro" ? "#00D4FF30" : "#A78BFA30"}`,
                          }}
                        >
                          {type.tier}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm font-semibold text-cyber-text mb-1">{type.label}</p>
                    <p className="text-xs text-cyber-muted">{type.desc}</p>
                    {selected && (
                      <div className="mt-2 h-0.5 rounded-full" style={{ background: `linear-gradient(90deg, ${type.color}, transparent)` }} />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Modules */}
          <div className="cyber-card p-6 space-y-4">
            <h3 className="text-sm font-semibold text-cyber-text">Scan Modules</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {modules.map((mod) => {
                const enabled = selectedModules.includes(mod.id);
                return (
                  <label
                    key={mod.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      enabled
                        ? "border-cyber-cyan/30 bg-cyber-cyan/5"
                        : "border-cyber-border hover:border-cyber-cyan/20"
                    } ${mod.pro ? "opacity-70" : ""}`}
                  >
                    <div className="relative mt-0.5">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={() => toggleModule(mod.id)}
                        className="sr-only"
                      />
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${
                          enabled ? "bg-cyber-cyan border-cyber-cyan" : "bg-transparent border-cyber-border"
                        }`}
                      >
                        {enabled && (
                          <svg className="w-2.5 h-2.5 text-cyber-bg" viewBox="0 0 10 10" fill="none">
                            <path d="M2 5l2.5 2.5 3.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-semibold text-cyber-text">{mod.label}</p>
                        {mod.pro && (
                          <span className="badge badge-info" style={{ fontSize: "10px", padding: "1px 6px" }}>Pro</span>
                        )}
                      </div>
                      <p className="text-xs text-cyber-muted">{mod.desc}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Submit */}
          <button
            id="new-scan-submit-btn"
            type="submit"
            className="btn-cyber w-full flex items-center justify-center gap-2 py-4 text-base font-bold"
          >
            <ScanSearch className="w-5 h-5" />
            Start Scan
          </button>
        </form>
      )}
    </div>
  );
}
