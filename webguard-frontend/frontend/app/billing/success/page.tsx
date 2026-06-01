"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle2, Shield, ArrowRight, Loader2 } from "lucide-react";
import { apiGet } from "../../../lib/api";

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [newTier, setNewTier] = useState("free");

  const gateway = searchParams.get("gateway") || "Payment Gateway";
  const txn = searchParams.get("txn") || searchParams.get("session_id") || "N/A";

  useEffect(() => {
    async function syncUserPlan() {
      try {
        // Fetch fresh user profile from backend
        const res = await apiGet("auth/me/");
        if (res.ok) {
          const data = await res.json();
          // Update localStorage
          localStorage.setItem("wg-user", JSON.stringify(data));
          setNewTier(data.subscription_tier || "free");
        }
      } catch (err) {
        console.error("Failed to sync plan state", err);
      } finally {
        setLoading(false);
      }
    }
    syncUserPlan();
  }, []);

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 text-center space-y-6 animate-fade-in">
        <div className="w-20 h-20 bg-cyber-green/10 rounded-full border border-cyber-green/30 flex items-center justify-center mx-auto scan-line-anim">
          <CheckCircle2 className="w-10 h-10 text-cyber-green" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-cyber-text">Payment Successful!</h1>
          <p className="text-sm text-cyber-muted">
            Thank you for subscribing to WebGuard Pro.
          </p>
        </div>

        <div className="cyber-card p-6 text-left space-y-4 border border-cyber-green/20">
          <div className="flex justify-between border-b border-cyber-border pb-3 text-xs">
            <span className="text-cyber-muted">Payment Gateway</span>
            <span className="font-semibold text-cyber-text capitalize">{gateway}</span>
          </div>
          <div className="flex justify-between border-b border-cyber-border pb-3 text-xs">
            <span className="text-cyber-muted">Transaction Ref / ID</span>
            <span className="font-mono text-cyber-cyan truncate max-w-[200px]">{txn}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-cyber-muted">Active Plan</span>
            {loading ? (
              <Loader2 className="w-3.5 h-3.5 text-cyber-cyan animate-spin" />
            ) : (
              <span className="font-bold text-cyber-cyan capitalize flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-cyber-cyan" /> {newTier}
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => router.push("/dashboard/settings")}
          className="btn-cyber w-full py-3.5 text-sm font-bold flex items-center justify-center gap-2"
        >
          Return to Settings <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
