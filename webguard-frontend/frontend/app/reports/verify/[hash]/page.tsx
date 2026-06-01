"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Shield, CheckCircle2, AlertTriangle, ExternalLink, Calendar, Key, RefreshCw, BarChart2 } from "lucide-react";
import { apiGet } from "../../../../lib/api";

export default function VerifyReportPage({ params }: { params: { hash: string } }) {
  const hash = params.hash;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    async function verifyReport() {
      setLoading(true);
      setError("");
      try {
        const res = await apiGet(`reports/verify/${hash}/`, { skipAuth: true });
        const data = await res.json();
        
        if (!res.ok) {
          throw new Error(data.error || "Report verification failed. Invalid hash signature.");
        }
        
        setReport(data);
      } catch (err: any) {
        setError(err.message || "Could not verify report authenticity. Check connection or hash.");
      } finally {
        setLoading(false);
      }
    }

    if (hash) {
      verifyReport();
    } else {
      setError("Missing report hash verification parameter.");
      setLoading(false);
    }
  }, [hash]);

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg text-cyber-text font-sans relative overflow-x-hidden py-16 px-4">
      {/* Background Glow */}
      <div className="absolute top-10 left-10 w-[500px] h-[500px] bg-cyber-cyan/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-cyber-purple/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-3xl mx-auto relative z-10 animate-fade-in-up">
        {/* Logo and Brand */}
        <div className="text-center mb-10">
          <Link href="/" className="inline-flex items-center gap-2 mb-3 group">
            <Shield className="w-10 h-10 text-cyber-cyan group-hover:scale-110 transition-transform" />
            <span className="text-2xl font-black text-white tracking-wide">
              WebGuard <span className="text-cyber-cyan">Pro</span>
            </span>
          </Link>
          <p className="text-xs text-cyber-muted uppercase tracking-widest">
            Cryptographic Integrity & Verification Portal
          </p>
        </div>

        {loading ? (
          /* ── Loading State ──────────────────────────────── */
          <div className="cyber-card p-12 text-center space-y-4 shadow-cyber">
            <RefreshCw className="w-10 h-10 text-cyber-cyan animate-spin mx-auto" />
            <p className="text-sm text-cyber-muted font-medium">Verifying HMAC-SHA256 integrity signature...</p>
          </div>
        ) : error ? (
          /* ── Error State (Invalid/Modified) ─────────────── */
          <div className="cyber-card p-8 sm:p-10 border border-cyber-red/30 shadow-cyber space-y-6 text-center">
            <div className="w-16 h-16 bg-cyber-red/10 rounded-full flex items-center justify-center border border-cyber-red/30 mx-auto">
              <AlertTriangle className="w-8 h-8 text-cyber-red" />
            </div>
            <div className="space-y-2">
              <h1 className="text-xl font-bold text-white">Verification Failed</h1>
              <p className="text-sm text-cyber-muted max-w-md mx-auto leading-relaxed">
                This document signature has been tampered with or does not exist in the WebGuard Pro blockchain registry database.
              </p>
            </div>
            <div className="bg-cyber-red/5 border border-cyber-red/10 rounded-lg p-4 font-mono text-xs text-cyber-red break-all select-all">
              Checked Hash: {hash}
            </div>
            <div className="pt-2">
              <Link href="/" className="btn-outline-cyber px-6 py-2.5 text-xs font-semibold inline-block">
                Return to Home
              </Link>
            </div>
          </div>
        ) : (
          /* ── Success State (Genuine Report) ─────────────── */
          <div className="space-y-6">
            {/* Success Banner */}
            <div className="cyber-card p-6 border-cyber-green/30 bg-cyber-green/5 shadow-cyber flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left">
              <div className="w-12 h-12 bg-cyber-green/10 rounded-full flex items-center justify-center border border-cyber-green/30 flex-shrink-0 animate-ping-slow">
                <CheckCircle2 className="w-6 h-6 text-cyber-green" />
              </div>
              <div className="flex-1 space-y-0.5">
                <h1 className="text-lg font-bold text-white uppercase tracking-wide">Verified Genuine Audit Report</h1>
                <p className="text-xs text-cyber-green font-medium">
                  This report is certified authentic and matches the original security scan metadata.
                </p>
              </div>
              <span className="text-[10px] bg-cyber-green/10 text-cyber-green border border-cyber-green/20 rounded px-2.5 py-1 uppercase tracking-wider font-bold">
                Pass
              </span>
            </div>

            {/* Scan Metadata Card */}
            <div className="cyber-card p-6 sm:p-8 space-y-6 shadow-cyber">
              <h2 className="text-sm font-bold text-cyber-muted uppercase tracking-wider border-b border-cyber-border pb-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-cyber-cyan" /> Scan Target Details
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
                <div>
                  <span className="text-xs text-cyber-muted uppercase tracking-wide font-semibold block mb-1">Target URL</span>
                  <a href={report.target_url} target="_blank" rel="noopener noreferrer" className="text-cyber-cyan font-semibold flex items-center gap-1 hover:underline break-all">
                    {report.target_url} <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                  </a>
                </div>
                <div>
                  <span className="text-xs text-cyber-muted uppercase tracking-wide font-semibold block mb-1">Audit Date</span>
                  <p className="text-white font-medium flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-cyber-muted" />
                    {new Date(report.scan_date).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-cyber-muted uppercase tracking-wide font-semibold block mb-1">Scan Type</span>
                  <p className="text-white font-medium capitalize">{report.scan_type} Assessment</p>
                </div>
                <div>
                  <span className="text-xs text-cyber-muted uppercase tracking-wide font-semibold block mb-1">Overall Health Score</span>
                  <p className="text-cyber-green font-extrabold text-lg">{report.health_score}%</p>
                </div>
              </div>
            </div>

            {/* Score Breakdown Cards */}
            <div className="cyber-card p-6 sm:p-8 space-y-6 shadow-cyber">
              <h2 className="text-sm font-bold text-cyber-muted uppercase tracking-wider border-b border-cyber-border pb-3 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-cyber-cyan" /> Verified Category Scores
              </h2>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[
                  { label: "Security", score: report.security_score, color: "text-cyber-red" },
                  { label: "SEO Audit", score: report.seo_score, color: "text-cyber-green" },
                  { label: "Performance", score: report.performance_score, color: "text-cyber-orange" },
                  { label: "Code Quality", score: report.code_quality_score, color: "text-cyber-cyan" },
                  { label: "Accessibility", score: report.accessibility_score, color: "text-cyber-purple" },
                  { label: "Mobile Usability", score: report.mobile_score, color: "text-cyber-orange" }
                ].map((cat) => (
                  <div key={cat.label} className="bg-cyber-dark border border-cyber-border p-4 rounded-xl text-center flex flex-col justify-center">
                    <span className="text-xs text-cyber-muted block mb-1.5">{cat.label}</span>
                    <span className={`text-2xl font-black ${cat.color}`}>{cat.score} <span className="text-[10px] text-cyber-muted">/100</span></span>
                  </div>
                ))}
              </div>
            </div>

            {/* Signature Card */}
            <div className="cyber-card p-6 shadow-cyber space-y-3">
              <h2 className="text-xs font-bold text-cyber-muted uppercase tracking-wider flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-cyber-cyan" /> Cryptographic Integrity Signature (HMAC)
              </h2>
              <div className="bg-cyber-dark border border-cyber-border rounded-lg p-3 font-mono text-[11px] text-cyber-cyan break-all select-all">
                {hash}
              </div>
              <p className="text-[10px] text-cyber-muted leading-relaxed">
                This signature was compiled by hashing the scan ID, health score, and completion timestamp with a server-level secret key. Any alteration of the PDF content or values will invalidate the signature check.
              </p>
            </div>

            {/* CTA */}
            <div className="text-center pt-4">
              <Link href="/" className="btn-cyber px-8 py-3 text-xs font-bold">
                Audit Your Website Now
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
