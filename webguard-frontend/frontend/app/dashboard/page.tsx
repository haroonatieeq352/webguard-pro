"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ScanSearch, Shield, TrendingUp, AlertTriangle,
  CheckCircle2, Clock, ExternalLink, ArrowRight, Activity, Loader2
} from "lucide-react";
import { apiGet } from "../../lib/api";

const riskConfig = {
  high:     { label: "High",     cls: "badge-high" },
  medium:   { label: "Medium",   cls: "badge-medium" },
  low:      { label: "Low",      cls: "badge-pass" },
  none:     { label: "Low Risk", cls: "badge-pass" },
  scanning: { label: "Scanning", cls: "badge-info" },
};

/* ── Health Score Gauge (SVG) ────────────────────────────── */
function HealthGauge({ score }: { score: number }) {
  const r = 52;
  const circumference = 2 * Math.PI * r;
  const gap = circumference * 0.3;
  const trackLen = circumference - gap;
  const fillLen = trackLen * (score / 100);

  const color = score >= 80 ? "#2ED573" : score >= 60 ? "#FF6B35" : "#FF4757";

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-[126deg]" viewBox="0 0 120 120">
          {/* Track */}
          <circle
            cx="60" cy="60" r={r}
            fill="none"
            stroke="#1E2A3A"
            strokeWidth="10"
            strokeDasharray={`${trackLen} ${gap + 0.1}`}
            strokeLinecap="round"
          />
          {/* Fill */}
          <circle
            cx="60" cy="60" r={r}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeDasharray={`${fillLen} ${circumference - fillLen}`}
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 6px ${color}80)`, transition: "stroke-dasharray 1s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold text-cyber-text" style={{ color }}>
            {score}
          </span>
          <span className="text-xs text-cyber-muted font-medium">/ 100</span>
        </div>
      </div>
      <p className="text-sm font-semibold mt-1" style={{ color }}>
        {score >= 80 ? "Good" : score >= 60 ? "Fair" : "At Risk"}
      </p>
    </div>
  );
}

/* ── Skeleton ────────────────────────────────────────────── */
function SkeletonCard() {
  return (
    <div className="stat-card p-5 space-y-3">
      <div className="skeleton h-4 w-24" />
      <div className="skeleton h-8 w-16" />
      <div className="skeleton h-3 w-32" />
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────── */
export default function DashboardOverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState<number[]>([0, 0, 0, 0]);
  const [userName, setUserName] = useState("");
  const [greeting, setGreeting] = useState("Welcome");

  // Dynamic Scan States
  const [recentScans, setRecentScans] = useState<any[]>([]);
  const [overallHealth, setOverallHealth] = useState(0);
  const [categoryScores, setCategoryScores] = useState({
    security: 0,
    seo: 0,
    performance: 0,
  });

  const [statsData, setStatsData] = useState<any[]>([
    { label: "Total Scans",       value: 0,  icon: ScanSearch,   color: "#00D4FF", suffix: "" },
    { label: "Vulnerabilities",   value: 0,  icon: AlertTriangle, color: "#FF4757", suffix: "" },
    { label: "Sites Protected",   value: 0,  icon: Shield,        color: "#2ED573", suffix: "" },
    { label: "Avg. Health Score", value: 0,  icon: Activity,      color: "#A78BFA", suffix: "%" },
  ]);

  useEffect(() => {
    // 1. Get user name dynamically from localStorage
    const rawUser = localStorage.getItem("wg-user");
    if (rawUser) {
      try {
        const u = JSON.parse(rawUser);
        const name = u.full_name || u.email.split("@")[0];
        const firstName = name.split(" ")[0];
        setUserName(firstName);
      } catch (e) {
        console.error("Failed to parse user name", e);
      }
    }

    // 2. Set dynamic greeting based on hour of day
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 17) setGreeting("Good afternoon");
    else if (hour < 22) setGreeting("Good evening");
    else setGreeting("Good night");

    async function loadDashboardData() {
      try {
        const res = await apiGet("scans/history/");
        if (!res.ok) throw new Error("Failed to load scans.");
        const data = await res.json();
        const history = data.results || data || [];

        if (history.length > 0) {
          // Process recent scans
          const parsedRecent = history.slice(0, 5).map((s: any) => {
            const score = s.result ? s.result.health_score : 0;
            const dateStr = s.completed_at ? new Date(s.completed_at).toLocaleDateString() : "Just now";
            const vulns = s.vulnerability_count || 0;
            
            let risk: "low" | "medium" | "high" | "scanning" = "low";
            if (s.status === "running" || s.status === "pending") risk = "scanning";
            else if (vulns > 5) risk = "high";
            else if (vulns > 0) risk = "medium";

            return {
              id: s.id,
              url: s.url.replace(/https?:\/\/(www\.)?/, "").split("/")[0],
              score,
              vulns,
              status: s.status,
              date: dateStr,
              risk,
            };
          });

          setRecentScans(parsedRecent);

          // Compute stats
          const totalScans = history.length;
          const completedScans = history.filter((s: any) => s.status === "completed");
          const totalVulns = history.reduce((sum: number, s: any) => sum + (s.vulnerability_count || 0), 0);
          
          const uniqueDomains = new Set(
            history.map((s: any) => {
              try {
                return new URL(s.url).hostname;
              } catch {
                return s.url;
              }
            })
          ).size;

          const avgHealth = completedScans.length > 0
            ? Math.round(completedScans.reduce((sum: number, s: any) => sum + (s.result?.health_score || 0), 0) / completedScans.length)
            : 0;

          setOverallHealth(avgHealth);

          // Category averages
          const avgSec = completedScans.length > 0
            ? Math.round(completedScans.reduce((sum: number, s: any) => sum + (s.result?.security_score || 0), 0) / completedScans.length)
            : 0;
          const avgSeo = completedScans.length > 0
            ? Math.round(completedScans.reduce((sum: number, s: any) => sum + (s.result?.seo_score || 0), 0) / completedScans.length)
            : 0;
          const avgPerf = completedScans.length > 0
            ? Math.round(completedScans.reduce((sum: number, s: any) => sum + (s.result?.performance_score || 0), 0) / completedScans.length)
            : 0;

          setCategoryScores({
            security: avgSec,
            seo: avgSeo,
            performance: avgPerf,
          });

          const nextStats = [
            { label: "Total Scans",       value: totalScans,  icon: ScanSearch,   color: "#00D4FF", suffix: "" },
            { label: "Vulnerabilities",   value: totalVulns,  icon: AlertTriangle, color: "#FF4757", suffix: "" },
            { label: "Sites Protected",   value: uniqueDomains,  icon: Shield,        color: "#2ED573", suffix: "" },
            { label: "Avg. Health Score", value: avgHealth,  icon: Activity,      color: "#A78BFA", suffix: "%" },
          ];
          setStatsData(nextStats);

          // Animate stat counters
          nextStats.forEach((s, i) => {
            let current = 0;
            const step = Math.max(1, Math.ceil(s.value / 25));
            const interval = setInterval(() => {
              current = Math.min(current + step, s.value);
              setCounts((prev) => {
                const next = [...prev];
                next[i] = current;
                return next;
              });
              if (current >= s.value) clearInterval(interval);
            }, 30);
          });

        } else {
          // No history: keep zeros
          setCounts([0, 0, 0, 0]);
        }
      } catch (err) {
        console.error("Failed to load dashboard info", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-cyber-text">
            {userName ? `${greeting}, ${userName}` : greeting} 👋
          </h2>
          <p className="text-sm text-cyber-muted mt-0.5">
            Here&apos;s your security dashboard overview.
          </p>
        </div>
        <Link
          href="/dashboard/new-scan"
          id="overview-new-scan-btn"
          className="btn-cyber inline-flex items-center gap-2 px-5 py-2.5 text-sm font-bold w-fit"
        >
          <ScanSearch className="w-4 h-4" />
          New Scan
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? [0, 1, 2, 3].map((i) => <SkeletonCard key={i} />)
          : statsData.map((stat, i) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="stat-card p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center"
                      style={{ background: `${stat.color}15`, border: `1px solid ${stat.color}30` }}
                    >
                      <Icon className="w-5 h-5" style={{ color: stat.color }} />
                    </div>
                  </div>
                  <div
                    className="text-3xl font-extrabold mb-1 ticker"
                    style={{ color: stat.color }}
                  >
                    {counts[i]}{stat.suffix}
                  </div>
                  <p className="text-xs text-cyber-muted font-medium">{stat.label}</p>
                </div>
              );
            })}
      </div>

      {/* Health gauge + recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Score */}
        <div className="cyber-card p-6 flex flex-col items-center justify-center gap-4">
          <h3 className="text-sm font-semibold text-cyber-muted uppercase tracking-wider self-start">
            Overall Health Score
          </h3>
          {loading ? (
            <div className="w-36 h-36 skeleton rounded-full" />
          ) : (
            <HealthGauge score={overallHealth} />
          )}
          <div className="w-full space-y-2 mt-2">
            {[
              { label: "Security", score: categoryScores.security, color: "#FF4757" },
              { label: "SEO",      score: categoryScores.seo, color: "#2ED573" },
              { label: "Performance", score: categoryScores.performance, color: "#FF6B35" },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-cyber-muted">{item.label}</span>
                  <span className="font-medium" style={{ color: item.color }}>{item.score}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-cyber-border overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-1000"
                    style={{ width: loading ? "0%" : `${item.score}%`, backgroundColor: item.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Scans */}
        <div className="lg:col-span-2 cyber-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-cyber-muted uppercase tracking-wider">
              Recent Scans
            </h3>
            <Link
              href="/dashboard/history"
              className="text-xs text-cyber-cyan hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="skeleton h-10 w-10 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton h-3.5 w-32" />
                    <div className="skeleton h-3 w-20" />
                  </div>
                  <div className="skeleton h-6 w-16 rounded-full" />
                </div>
              ))}
            </div>
          ) : recentScans.length === 0 ? (
            <div className="text-center py-10 space-y-3">
              <p className="text-xs text-cyber-muted">No scan logs available.</p>
              <Link href="/dashboard/new-scan" className="text-xs text-cyber-cyan hover:underline">
                Run your first scan now →
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {recentScans.map((scan) => {
                const risk = riskConfig[scan.risk as keyof typeof riskConfig] || riskConfig.low;
                return (
                  <div
                    key={scan.id}
                    onClick={() => router.push(`/dashboard/results?id=${scan.id}`)}
                    className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-cyber-cyan/5 transition-colors cursor-pointer"
                  >
                    {/* Status icon */}
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      scan.status === "running" || scan.status === "pending"
                        ? "bg-cyber-cyan/10 border border-cyber-cyan/20 animate-pulse"
                        : "bg-cyber-card border border-cyber-border"
                    }`}>
                      {scan.status === "running" || scan.status === "pending" ? (
                        <Loader2 className="w-4 h-4 text-cyber-cyan animate-spin" />
                      ) : scan.score >= 70 ? (
                        <CheckCircle2 className="w-4 h-4 text-cyber-green" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-cyber-red" />
                      )}
                    </div>

                    {/* URL + date */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-cyber-text truncate flex items-center gap-1">
                        {scan.url}
                        <ExternalLink className="w-3 h-3 text-cyber-muted flex-shrink-0" />
                      </p>
                      <p className="text-xs text-cyber-muted flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {scan.date}
                        {scan.vulns > 0 && (
                          <span className="ml-2 text-cyber-red">• {scan.vulns} vulns</span>
                        )}
                      </p>
                    </div>

                    {/* Score + badge */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {scan.status === "completed" && (
                        <span className="text-sm font-bold" style={{
                          color: scan.score >= 70 ? "#2ED573" : scan.score >= 50 ? "#FF6B35" : "#FF4757"
                        }}>
                          {scan.score}
                        </span>
                      )}
                      <span className={`badge ${risk.cls}`}>{risk.label}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Run Security Scan",  desc: "OWASP Top 10 check",      href: "/dashboard/new-scan",  icon: Shield,       color: "#FF4757" },
          { label: "Check SEO Health",   desc: "Audit meta & structure",   href: "/dashboard/new-scan",  icon: TrendingUp,   color: "#2ED573" },
          { label: "View Latest Report", desc: "Download PDF report",      href: "/dashboard/results",   icon: CheckCircle2, color: "#00D4FF" },
        ].map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.label}
              href={action.href}
              className="cyber-card p-4 flex items-center gap-3 hover:border-cyber-cyan/30 group"
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: `${action.color}15`, border: `1px solid ${action.color}30` }}
              >
                <Icon className="w-5 h-5" style={{ color: action.color }} />
              </div>
              <div>
                <p className="text-sm font-semibold text-cyber-text group-hover:text-cyber-cyan transition-colors">
                  {action.label}
                </p>
                <p className="text-xs text-cyber-muted">{action.desc}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-cyber-muted group-hover:text-cyber-cyan ml-auto transition-colors" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
