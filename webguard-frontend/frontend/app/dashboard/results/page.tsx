"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Shield, TrendingUp, Zap, Code2, Accessibility, Smartphone,
  ChevronDown, ChevronUp, Download, RefreshCw, ExternalLink,
  AlertTriangle, CheckCircle2, Info, XCircle, Loader2, AlertCircle, ArrowRight
} from "lucide-react";
import { apiGet, apiPost } from "../../../lib/api";

const severityConfig = {
  critical: { cls: "badge-critical", label: "Critical", icon: XCircle,       color: "#FF1744" },
  high:     { cls: "badge-high",     label: "High",     icon: AlertTriangle,  color: "#FF4757" },
  medium:   { cls: "badge-medium",   label: "Medium",   icon: AlertTriangle,  color: "#FF6B35" },
  low:      { cls: "badge-low",      label: "Low",      icon: Info,           color: "#FFD60A" },
  pass:     { cls: "badge-pass",     label: "Pass",     icon: CheckCircle2,   color: "#2ED573" },
};

/* ── Score arc SVG ───────────────────────────────────────── */
function ScoreArc({ score, color }: { score: number; color: string }) {
  const r = 28;
  const c = 2 * Math.PI * r;
  const fill = c * (score / 100);
  return (
    <svg width="68" height="68" viewBox="0 0 68 68" className="-rotate-90">
      <circle cx="34" cy="34" r={r} fill="none" stroke="#1E2A3A" strokeWidth="6" />
      <circle
        cx="34" cy="34" r={r}
        fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={`${fill} ${c - fill}`}
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 4px ${color}80)` }}
      />
    </svg>
  );
}

/* ── Vulnerability Row ───────────────────────────────────── */
function VulnRow({ vuln }: { vuln: any }) {
  const [open, setOpen] = useState(false);
  const severityKey = (vuln.severity || "info").toLowerCase() as keyof typeof severityConfig;
  const s = severityConfig[severityKey] || severityConfig.low;
  const Icon = s.icon;

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${open ? "border-cyber-cyan/20" : "border-cyber-border"}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-cyber-cyan/5 transition-colors"
      >
        <Icon className="w-4 h-4 flex-shrink-0" style={{ color: s.color }} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-cyber-text">{vuln.title}</span>
            <span className={`badge ${s.cls}`}>{s.label}</span>
            {vuln.owasp_category && vuln.owasp_category !== "N/A" && (
              <span className="badge badge-info">{vuln.owasp_category}</span>
            )}
          </div>
          <p className="text-xs text-cyber-muted truncate mt-0.5">{vuln.url}</p>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-cyber-muted flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-cyber-muted flex-shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-2 border-t border-cyber-border space-y-3 animate-fade-in">
          <div>
            <p className="text-xs font-semibold text-cyber-muted uppercase tracking-wider mb-1">Description</p>
            <p className="text-sm text-cyber-text">{vuln.description}</p>
          </div>
          {vuln.evidence && (
            <div>
              <p className="text-xs font-semibold text-cyber-muted uppercase tracking-wider mb-1">Evidence</p>
              <code className="text-xs text-cyber-cyan bg-cyber-bg px-3 py-2 rounded-lg block font-mono whitespace-pre-wrap break-all">
                {vuln.evidence}
              </code>
            </div>
          )}
          {vuln.remediation && (
            <div>
              <p className="text-xs font-semibold text-cyber-muted uppercase tracking-wider mb-1">Fix</p>
              <p className="text-sm text-cyber-green">{vuln.remediation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Content Component ────────────────────────────────────── */
function ResultsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const scanId = searchParams.get("id");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [scan, setScan] = useState<any>(null);
  const [vulnerabilities, setVulnerabilities] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [rescanLoading, setRescanLoading] = useState(false);
  
  // PDF download states
  const [pdfLoading, setPdfLoading] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pdfMessage, setPdfMessage] = useState("");

  useEffect(() => {
    let isChecking = true;
    let pollInterval: NodeJS.Timeout | null = null;

    async function loadData() {
      setLoading(true);
      setError("");
      try {
        let activeId = scanId;

        // If no ID is passed, fetch latest from history
        if (!activeId) {
          const historyRes = await apiGet("scans/history/");
          if (!historyRes.ok) {
            throw new Error("Failed to load scan history.");
          }
          const historyData = await historyRes.json();
          if (historyData.results && historyData.results.length > 0) {
            activeId = historyData.results[0].id;
          } else {
            // No scans found
            setScan(null);
            setLoading(false);
            return;
          }
        }

        const res = await apiGet(`scans/results/${activeId}/`);
        if (!res.ok) {
          throw new Error("Could not retrieve scan results.");
        }
        const data = await res.json();
        setScan(data.scan);
        setVulnerabilities(data.vulnerabilities || []);

        // Start polling if pending or running
        if (data.scan.status === "pending" || data.scan.status === "running") {
          pollInterval = setInterval(async () => {
            if (!isChecking) return;
            try {
              const pollRes = await apiGet(`scans/results/${activeId}/`);
              if (pollRes.ok) {
                const pollData = await pollRes.json();
                setScan(pollData.scan);
                setVulnerabilities(pollData.vulnerabilities || []);

                if (pollData.scan.status === "completed" || pollData.scan.status === "failed") {
                  if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                  }
                }
              }
            } catch (err) {
              // Ignore polling network failures
            }
          }, 3000);
        }
      } catch (err: any) {
        setError(err.message || "An error occurred while loading results.");
      } finally {
        setLoading(false);
      }
    }

    loadData();

    return () => {
      isChecking = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [scanId]);

  async function handleRescan() {
    if (!scan) return;
    setRescanLoading(true);
    try {
      router.push(`/dashboard/new-scan?url=${encodeURIComponent(scan.url)}&type=${scan.scan_type}`);
    } catch (err) {
      setRescanLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!scan) return;
    setPdfLoading(true);
    setPdfMessage("");
    try {
      const res = await apiGet(`reports/${scan.id}/`);
      if (res.status === 403) {
        // Enforce Pro/Business/Enterprise only warnings
        setShowUpgradeModal(true);
        setPdfLoading(false);
        return;
      }
      if (res.status === 404) {
        // Report not ready yet or S3 error
        setPdfMessage("PDF Report has not been compiled yet or your tier doesn't support PDF downloads. Please wait a few seconds and try again.");
        setPdfLoading(false);
        return;
      }
      if (!res.ok) {
        throw new Error("Failed to generate PDF URL.");
      }
      const data = await res.json();
      if (data.pdf_url) {
        window.open(data.pdf_url, "_blank");
      } else {
        setPdfMessage("Invalid PDF download link generated.");
      }
    } catch (err) {
      setPdfMessage("Failed to fetch report PDF link.");
    } finally {
      setPdfLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-cyber-card border border-cyber-border rounded-xl w-1/3" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="h-64 bg-cyber-card border border-cyber-border rounded-xl" />
          <div className="lg:col-span-3 h-64 bg-cyber-card border border-cyber-border rounded-xl" />
        </div>
        <div className="h-96 bg-cyber-card border border-cyber-border rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="cyber-card p-8 text-center space-y-4 border border-cyber-red/20 max-w-xl mx-auto">
        <XCircle className="w-12 h-12 text-cyber-red mx-auto" />
        <div>
          <h3 className="text-lg font-bold text-cyber-text">Failed to Load Results</h3>
          <p className="text-sm text-cyber-muted mt-1">{error}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn-cyber px-4 py-2 text-xs font-bold inline-flex items-center gap-1"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="cyber-card p-12 text-center space-y-6 border border-cyber-cyan/10 max-w-xl mx-auto my-12">
        <div className="w-16 h-16 bg-cyber-cyan/5 rounded-full border border-cyber-cyan/20 flex items-center justify-center mx-auto">
          <Shield className="w-8 h-8 text-cyber-cyan" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-bold text-cyber-text">No Scans Found</h3>
          <p className="text-sm text-cyber-muted max-w-md mx-auto">
            You haven't run any website security checks yet. Start scanning now to find vulnerabilities and optimize your SEO scores.
          </p>
        </div>
        <a
          href="/dashboard/new-scan"
          className="btn-cyber px-6 py-3 text-sm font-bold inline-flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Run Your First Scan
        </a>
      </div>
    );
  }

  if (scan.status === "pending" || scan.status === "running") {
    return (
      <div className="max-w-xl mx-auto py-12 space-y-6 text-center animate-fade-in">
        <div className="cyber-card p-8 border border-cyber-cyan/30 space-y-5">
          <div className="w-16 h-16 mx-auto bg-cyber-cyan/10 rounded-full border border-cyber-cyan/20 flex items-center justify-center scan-line-anim">
            <Loader2 className="w-8 h-8 text-cyber-cyan animate-spin" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-cyber-text">Scan in Progress</h3>
            <p className="text-sm text-cyber-muted">
              WebGuard Pro is actively auditing <span className="text-cyber-cyan font-mono break-all">{scan.url}</span>.
            </p>
            <p className="text-xs text-cyber-muted uppercase tracking-wider font-semibold">
              Status: {scan.status}
            </p>
          </div>
          <div className="pt-4 border-t border-cyber-border/40 text-xs text-cyber-muted">
            This page will automatically update once the scan is complete. You can also leave this page and check back later in your History.
          </div>
        </div>
      </div>
    );
  }

  if (scan.status === "failed") {
    return (
      <div className="max-w-xl mx-auto py-12 space-y-6 text-center animate-fade-in">
        <div className="cyber-card p-8 border border-cyber-red/30 space-y-5">
          <div className="w-16 h-16 mx-auto bg-cyber-red/10 rounded-full border border-cyber-red/20 flex items-center justify-center">
            <XCircle className="w-8 h-8 text-cyber-red" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-cyber-text">Scan Failed</h3>
            <p className="text-sm text-cyber-muted">
              The scan engine encountered an issue while checking <span className="text-cyber-cyan font-mono break-all">{scan.url}</span>.
            </p>
            <p className="text-xs text-cyber-red font-semibold">
              Please verify that the domain is correct, public, and reachable.
            </p>
          </div>
          <a
            href="/dashboard/new-scan"
            className="btn-cyber py-2 px-4 text-xs font-bold inline-flex items-center gap-1.5"
          >
            Try Again
          </a>
        </div>
      </div>
    );
  }

  const result = scan.result || {
    health_score: 0,
    seo_score: 0,
    security_score: 0,
    performance_score: 0,
    code_quality_score: 0,
    accessibility_score: 0,
    mobile_score: 0
  };

  const overall = result.health_score;
  const overallColor = overall >= 70 ? "#2ED573" : overall >= 50 ? "#FF6B35" : "#FF4757";

  const categories = [
    { label: "Security",      score: result.security_score, icon: Shield,        color: "#FF4757", weight: "25%" },
    { label: "SEO",           score: result.seo_score, icon: TrendingUp,    color: "#2ED573", weight: "20%" },
    { label: "Performance",   score: result.performance_score, icon: Zap,           color: "#FF6B35", weight: "20%" },
    { label: "Code Quality",  score: result.code_quality_score, icon: Code2,         color: "#00D4FF", weight: "15%" },
    { label: "Accessibility", score: result.accessibility_score, icon: Accessibility, color: "#A78BFA", weight: "10%" },
    { label: "Mobile",        score: result.mobile_score, icon: Smartphone,    color: "#FFD60A", weight: "10%" },
  ];

  const vulnCounts = {
    critical: vulnerabilities.filter((v) => v.severity === "critical").length,
    high:     vulnerabilities.filter((v) => v.severity === "high").length,
    medium:   vulnerabilities.filter((v) => v.severity === "medium").length,
    low:      vulnerabilities.filter((v) => v.severity === "low").length,
    pass:     vulnerabilities.filter((v) => v.severity === "pass").length,
  };

  const filtered =
    filter === "all"
      ? vulnerabilities
      : vulnerabilities.filter((v) => v.severity === filter);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-cyber-text">Scan Results</h2>
            <CheckCircle2 className="w-5 h-5 text-cyber-green" />
          </div>
          <a
            href={scan.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-cyber-cyan flex items-center gap-1 hover:underline break-all"
          >
            {scan.url} <ExternalLink className="w-3 h-3" />
          </a>
          <p className="text-xs text-cyber-muted mt-1">
            Scanned: {new Date(scan.completed_at || scan.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            id="results-rescan-btn"
            onClick={handleRescan}
            disabled={rescanLoading}
            className="btn-outline-cyber flex items-center gap-2 px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {rescanLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Re-scan
          </button>
          <button
            id="results-download-pdf-btn"
            onClick={handleDownloadPdf}
            disabled={pdfLoading}
            className="btn-cyber flex items-center gap-2 px-4 py-2 text-sm font-bold disabled:opacity-60"
          >
            {pdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            PDF Report
          </button>
        </div>
      </div>

      {pdfMessage && (
        <div className="p-3.5 bg-cyber-cyan/5 border border-cyber-cyan/30 rounded-lg flex items-start gap-3 animate-fade-in text-cyber-cyan text-sm">
          <Info className="w-4.5 h-4.5 mt-0.5 flex-shrink-0" />
          <p>{pdfMessage}</p>
        </div>
      )}

      {/* Overall score + categories */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Big score */}
        <div className="cyber-card p-6 flex flex-col items-center justify-center gap-2">
          <p className="text-xs text-cyber-muted uppercase tracking-wider font-semibold">Health Score</p>
          <div className="relative my-2">
            <svg className="-rotate-90 w-32 h-32" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" fill="none" stroke="#1E2A3A" strokeWidth="10" />
              <circle
                cx="60" cy="60" r="52"
                fill="none" stroke={overallColor} strokeWidth="10"
                strokeDasharray={`${(2 * Math.PI * 52) * (overall / 100)} ${2 * Math.PI * 52}`}
                strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 8px ${overallColor}80)` }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-extrabold" style={{ color: overallColor }}>{overall}</span>
              <span className="text-xs text-cyber-muted">/ 100</span>
            </div>
          </div>
          <p className="text-sm font-semibold" style={{ color: overallColor }}>
            {overall >= 70 ? "Good" : overall >= 50 ? "Fair" : "At Risk"}
          </p>
          {/* Severity summary */}
          <div className="w-full mt-3 grid grid-cols-2 gap-1.5">
            {Object.entries(vulnCounts).map(([sev, count]) => (
              <div key={sev} className="flex items-center gap-1.5 text-xs">
                <span className={`badge ${severityConfig[sev as keyof typeof severityConfig]?.cls || "badge-low"} text-[10px] px-1.5`}>
                  {sev}
                </span>
                <span className="font-bold text-cyber-text">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Category breakdown */}
        <div className="lg:col-span-3 cyber-card p-6">
          <h3 className="text-sm font-semibold text-cyber-muted uppercase tracking-wider mb-4">
            Category Breakdown
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {categories.map((cat) => {
              const Icon = cat.icon;
              return (
                <div key={cat.label} className="flex items-center gap-3">
                  <div className="relative flex-shrink-0">
                    <ScoreArc score={cat.score} color={cat.color} />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-bold" style={{ color: cat.color }}>{cat.score}</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-0.5">
                      <Icon className="w-3.5 h-3.5" style={{ color: cat.color }} />
                      <span className="text-xs font-semibold text-cyber-text">{cat.label}</span>
                    </div>
                    <span className="text-xs text-cyber-muted">Weight: {cat.weight}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Vulnerability list */}
      <div className="cyber-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <h3 className="text-sm font-semibold text-cyber-muted uppercase tracking-wider">
            Vulnerabilities &amp; Findings
          </h3>
          {/* Severity filter */}
          <div className="flex flex-wrap gap-2 sm:ml-auto">
            {["all", "critical", "high", "medium", "low", "pass"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  filter === f
                    ? "bg-cyber-cyan text-cyber-bg"
                    : "bg-cyber-card border border-cyber-border text-cyber-muted hover:border-cyber-cyan/30"
                }`}
              >
                {f === "all" ? `All (${vulnerabilities.length})` : (
                  <>
                    {f.charAt(0).toUpperCase() + f.slice(1)}{" "}
                    ({vulnCounts[f as keyof typeof vulnCounts] || 0})
                  </>
                )}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-cyber-muted p-4 text-center">No vulnerabilities found matching this filter.</p>
          ) : (
            filtered.map((vuln) => (
              <VulnRow key={vuln.id} vuln={vuln} />
            ))
          )}
        </div>
      </div>

      {/* Upgrade Plan Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="cyber-card max-w-md w-full p-6 border border-cyber-cyan/40 space-y-5 shadow-cyber relative">
            <button
              onClick={() => setShowUpgradeModal(false)}
              className="absolute right-4 top-4 text-cyber-muted hover:text-cyber-cyan transition-colors"
            >
              ✕
            </button>
            <div className="w-12 h-12 bg-cyber-cyan/10 rounded-full border border-cyber-cyan/30 flex items-center justify-center">
              <Download className="w-6 h-6 text-cyber-cyan animate-pulse" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-cyber-text">Unlock PDF Reports</h3>
              <p className="text-sm text-cyber-muted leading-relaxed">
                Detailed white-label PDF downloads, signature checks, and full reports are exclusive features of our premium tiers (Pro, Business, and Enterprise).
              </p>
            </div>
            <ul className="space-y-2 text-xs text-cyber-muted border-y border-cyber-border py-4">
              <li className="flex items-center gap-2">✓ Executive summary dashboard reports</li>
              <li className="flex items-center gap-2">✓ Cryptographic HMAC integrity check verification</li>
              <li className="flex items-center gap-2">✓ Professional, print-friendly presentation layout</li>
            </ul>
            <div className="flex gap-3">
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="btn-outline-cyber flex-1 py-2.5 text-xs font-semibold"
              >
                Maybe Later
              </button>
              <button
                onClick={() => router.push("/dashboard/settings")}
                className="btn-cyber flex-1 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5"
              >
                Upgrade Plan <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ScanResultsPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen bg-cyber-bg items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ResultsContent />
    </Suspense>
  );
}
