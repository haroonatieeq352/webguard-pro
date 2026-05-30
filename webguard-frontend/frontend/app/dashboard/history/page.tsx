"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Search, ScanSearch, Trash2, Download, Eye,
  ChevronUp, ChevronDown, ChevronsUpDown, AlertTriangle, CheckCircle2,
  Loader2, Filter, XCircle, Info
} from "lucide-react";
import { apiGet, apiDelete } from "../../../lib/api";

type SortKey = "url" | "score" | "vulns" | "date" | "status";
type SortDir = "asc" | "desc";

function HistoryContent() {
  const router = useRouter();
  
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  const [search, setSearch]     = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortKey, setSortKey]   = useState<SortKey>("date");
  const [sortDir, setSortDir]   = useState<SortDir>("desc");
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage]         = useState(1);
  const PER_PAGE = 6;

  // PDF report states
  const [pdfLoadingId, setPdfLoadingId] = useState<string | null>(null);
  const [pdfMessage, setPdfMessage] = useState("");
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      setError("");
      try {
        const res = await apiGet("scans/history/");
        if (!res.ok) {
          throw new Error("Failed to retrieve scan history.");
        }
        const data = await res.json();
        // Since backend has default pagination, read data.results
        setScans(data.results || data || []);
      } catch (err: any) {
        setError(err.message || "Failed to load scan history.");
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("asc"); }
    setPage(1);
  }

  const processedScans = useMemo(() => {
    return scans.map((s: any) => {
      const score = s.result ? s.result.health_score : 0;
      const dateStr = s.created_at ? s.created_at.split("T")[0] : "—";
      const displayType = s.scan_type === "quick" ? "Quick" : s.scan_type === "deep" ? "Deep" : "Full";
      return {
        id: s.id,
        url: s.url,
        score,
        vulns: s.vulnerability_count || 0,
        status: s.status, // 'pending', 'running', 'completed', 'failed'
        date: dateStr,
        type: displayType,
      };
    });
  }, [scans]);

  const filtered = useMemo(() => {
    return processedScans
      .filter((s) => {
        const matchSearch = s.url.toLowerCase().includes(search.toLowerCase());
        const matchStatus =
          statusFilter === "all" ||
          (statusFilter === "complete" && s.status === "completed") ||
          (statusFilter === "scanning" && (s.status === "running" || s.status === "pending")) ||
          (statusFilter === "failed" && s.status === "failed");
        return matchSearch && matchStatus;
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortKey === "url")    cmp = a.url.localeCompare(b.url);
        if (sortKey === "score")  cmp = a.score - b.score;
        if (sortKey === "vulns")  cmp = a.vulns - b.vulns;
        if (sortKey === "date")   cmp = a.date.localeCompare(b.date);
        if (sortKey === "status") cmp = a.status.localeCompare(b.status);
        return sortDir === "asc" ? cmp : -cmp;
      });
  }, [processedScans, search, statusFilter, sortKey, sortDir]);

  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const paginated  = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  function toggleSelect(id: string) {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  }

  function toggleSelectAll() {
    if (selected.length === paginated.length) setSelected([]);
    else setSelected(paginated.map((s) => s.id));
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to delete this scan request from history?")) return;
    try {
      const res = await apiDelete(`scans/delete/${id}/`);
      if (res.ok) {
        setScans((prev) => prev.filter((s) => s.id !== id));
        setSelected((prev) => prev.filter((x) => x !== id));
      } else {
        alert("Failed to delete the scan.");
      }
    } catch (err) {
      alert("Error occurred deleting scan request.");
    }
  }

  async function handleDownloadPdf(id: string) {
    setPdfLoadingId(id);
    setPdfMessage("");
    try {
      const res = await apiGet(`reports/${id}/`);
      if (res.status === 403) {
        setShowUpgradeModal(true);
        setPdfLoadingId(null);
        return;
      }
      if (res.status === 404) {
        setPdfMessage("PDF Report has not been compiled yet or your tier doesn't support PDF downloads.");
        setPdfLoadingId(null);
        return;
      }
      if (!res.ok) {
        throw new Error("Failed to get report PDF link.");
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
      setPdfLoadingId(null);
    }
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <ChevronsUpDown className="w-3.5 h-3.5 text-cyber-muted" />;
    return sortDir === "asc"
      ? <ChevronUp className="w-3.5 h-3.5 text-cyber-cyan" />
      : <ChevronDown className="w-3.5 h-3.5 text-cyber-cyan" />;
  }

  const scoreColor = (s: number) =>
    s === 0 ? "#94A3B8" : s >= 70 ? "#2ED573" : s >= 50 ? "#FF6B35" : "#FF4757";

  if (loading) {
    return (
      <div className="space-y-5 animate-pulse">
        <div className="h-12 bg-cyber-card border border-cyber-border rounded-xl w-1/4" />
        <div className="h-16 bg-cyber-card border border-cyber-border rounded-xl" />
        <div className="h-96 bg-cyber-card border border-cyber-border rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="cyber-card p-8 text-center space-y-4 border border-cyber-red/20 max-w-xl mx-auto my-12">
        <XCircle className="w-12 h-12 text-cyber-red mx-auto" />
        <div>
          <h3 className="text-lg font-bold text-cyber-text">Failed to Load History</h3>
          <p className="text-sm text-cyber-muted mt-1">{error}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn-cyber px-4 py-2 text-xs font-bold inline-flex items-center gap-1"
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Reload
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div>
          <h2 className="text-xl font-bold text-cyber-text">Scan History</h2>
          <p className="text-sm text-cyber-muted">{scans.length} total scans</p>
        </div>
        <Link
          href="/dashboard/new-scan"
          className="btn-cyber sm:ml-auto inline-flex items-center gap-2 px-4 py-2.5 text-sm font-bold w-fit"
        >
          <ScanSearch className="w-4 h-4" /> New Scan
        </Link>
      </div>

      {pdfMessage && (
        <div className="p-3.5 bg-cyber-cyan/5 border border-cyber-cyan/30 rounded-lg flex items-start gap-3 animate-fade-in text-cyber-cyan text-sm">
          <Info className="w-4.5 h-4.5 mt-0.5 flex-shrink-0" />
          <p>{pdfMessage}</p>
        </div>
      )}

      {/* Filters */}
      <div className="cyber-card p-4 flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
          <input
            id="history-search"
            type="search"
            placeholder="Search by URL..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="scan-input w-full pl-9 pr-4 py-2.5 text-sm"
          />
        </div>
        {/* Status filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-cyber-muted flex-shrink-0" />
          {["all", "complete", "scanning", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === s
                  ? "bg-cyber-cyan text-cyber-bg"
                  : "border border-cyber-border text-cyber-muted hover:border-cyber-cyan/30"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="cyber-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cyber-border">
                <th className="p-4 w-10">
                  <div
                    className={`w-4 h-4 rounded border flex items-center justify-center cursor-pointer ${
                      selected.length === paginated.length && paginated.length > 0
                        ? "bg-cyber-cyan border-cyber-cyan"
                        : "border-cyber-border hover:border-cyber-cyan/50"
                    }`}
                    onClick={toggleSelectAll}
                  >
                    {selected.length === paginated.length && paginated.length > 0 && (
                      <svg className="w-2.5 h-2.5 text-cyber-bg" viewBox="0 0 10 10" fill="none">
                        <path d="M2 5l2.5 2.5 3.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    )}
                  </div>
                </th>
                {(["url", "score", "vulns", "status", "date"] as SortKey[]).map((col) => (
                  <th
                    key={col}
                    className="p-4 text-left text-xs font-semibold text-cyber-muted uppercase tracking-wider cursor-pointer hover:text-cyber-cyan transition-colors select-none"
                    onClick={() => handleSort(col)}
                  >
                    <div className="flex items-center gap-1.5">
                      {col === "url" ? "URL" : col === "vulns" ? "Vulnerabilities" : col.charAt(0).toUpperCase() + col.slice(1)}
                      <SortIcon col={col} />
                    </div>
                  </th>
                ))}
                <th className="p-4 text-left text-xs font-semibold text-cyber-muted uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-10 text-center text-cyber-muted text-sm">
                    No scans found matching your filters.
                  </td>
                </tr>
              ) : (
                paginated.map((scan) => (
                  <tr
                    key={scan.id}
                    className={`border-b border-cyber-border/50 hover:bg-cyber-cyan/5 transition-colors ${
                      selected.includes(scan.id) ? "bg-cyber-cyan/5" : ""
                    }`}
                  >
                    {/* Checkbox */}
                    <td className="p-4">
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center cursor-pointer ${
                          selected.includes(scan.id)
                            ? "bg-cyber-cyan border-cyber-cyan"
                            : "border-cyber-border hover:border-cyber-cyan/50"
                        }`}
                        onClick={() => toggleSelect(scan.id)}
                      >
                        {selected.includes(scan.id) && (
                          <svg className="w-2.5 h-2.5 text-cyber-bg" viewBox="0 0 10 10" fill="none">
                            <path d="M2 5l2.5 2.5 3.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          </svg>
                        )}
                      </div>
                    </td>
                    {/* URL */}
                    <td className="p-4">
                      <div className="max-w-[200px] sm:max-w-xs md:max-w-sm truncate">
                        <p className="font-medium text-cyber-text truncate" title={scan.url}>{scan.url}</p>
                        <p className="text-xs text-cyber-muted">{scan.type} Scan</p>
                      </div>
                    </td>
                    {/* Score */}
                    <td className="p-4">
                      <span className="text-base font-bold" style={{ color: scoreColor(scan.score) }}>
                        {scan.status === "running" || scan.status === "pending" ? "—" : scan.score}
                      </span>
                    </td>
                    {/* Vulns */}
                    <td className="p-4">
                      {scan.vulns > 0 ? (
                        <span className="flex items-center gap-1 text-cyber-red font-medium">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          {scan.vulns}
                        </span>
                      ) : scan.status === "running" || scan.status === "pending" ? (
                        <span className="text-cyber-muted">—</span>
                      ) : (
                        <span className="flex items-center gap-1 text-cyber-green">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          0
                        </span>
                      )}
                    </td>
                    {/* Status */}
                    <td className="p-4">
                      {scan.status === "running" || scan.status === "pending" ? (
                        <span className="badge badge-info flex items-center gap-1 w-fit">
                          <Loader2 className="w-3 h-3 animate-spin" /> Scanning
                        </span>
                      ) : scan.status === "failed" ? (
                        <span className="badge badge-high">Failed</span>
                      ) : (
                        <span className="badge badge-pass">Complete</span>
                      )}
                    </td>
                    {/* Date */}
                    <td className="p-4 text-cyber-muted text-xs">{scan.date}</td>
                    {/* Actions */}
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => router.push(`/dashboard/results?id=${scan.id}`)}
                          className="p-1.5 text-cyber-muted hover:text-cyber-cyan transition-colors rounded-lg hover:bg-cyber-cyan/10"
                          title="View results"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDownloadPdf(scan.id)}
                          disabled={pdfLoadingId === scan.id || scan.status !== "completed"}
                          className="p-1.5 text-cyber-muted hover:text-cyber-cyan transition-colors rounded-lg hover:bg-cyber-cyan/10 disabled:opacity-30"
                          title="Download PDF"
                        >
                          {pdfLoadingId === scan.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleDelete(scan.id)}
                          className="p-1.5 text-cyber-muted hover:text-cyber-red transition-colors rounded-lg hover:bg-cyber-red/10"
                          title="Delete scan"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-cyber-border">
            <p className="text-xs text-cyber-muted">
              Showing {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, filtered.length)} of {filtered.length}
            </p>
            <div className="flex gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                    p === page
                      ? "bg-cyber-cyan text-cyber-bg"
                      : "text-cyber-muted hover:text-cyber-text hover:bg-cyber-cyan/10"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
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
            <div className="flex gap-3">
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="btn-outline-cyber flex-1 py-2.5 text-xs font-semibold"
              >
                Maybe Later
              </button>
              <button
                onClick={() => router.push("/dashboard/settings")}
                className="btn-cyber flex-1 py-2.5 text-xs font-bold"
              >
                Upgrade Plan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ScanHistoryPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen bg-cyber-bg items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <HistoryContent />
    </Suspense>
  );
}
