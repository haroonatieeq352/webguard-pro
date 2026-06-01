"use client";

import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { XCircle, ArrowLeft, RefreshCw } from "lucide-react";

function FailureContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const gateway = searchParams.get("gateway") || "Payment Gateway";
  const code = searchParams.get("code") || "UNKNOWN_ERROR";
  const txn = searchParams.get("txn") || "N/A";

  // Translate common gateway failure codes for professional styling
  let userFriendlyExplanation = "The payment transaction was cancelled or declined by the provider.";
  if (code === "112") {
    userFriendlyExplanation = "Insufficient funds in your account. Please top up your wallet and try again.";
  } else if (code === "121" || code === "116") {
    userFriendlyExplanation = "Authentication failed or the MPIN was entered incorrectly.";
  } else if (code === "005") {
    userFriendlyExplanation = "Transaction declined by the card issuer or account holder.";
  }

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-red/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 text-center space-y-6 animate-fade-in">
        <div className="w-20 h-20 bg-cyber-red/10 rounded-full border border-cyber-red/30 flex items-center justify-center mx-auto scan-line-anim">
          <XCircle className="w-10 h-10 text-cyber-red" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-cyber-text">Payment Failed</h1>
          <p className="text-sm text-cyber-muted">
            The transaction could not be processed successfully.
          </p>
        </div>

        <div className="cyber-card p-6 text-left space-y-4 border border-cyber-red/20">
          <div className="flex justify-between border-b border-cyber-border pb-3 text-xs">
            <span className="text-cyber-muted">Payment Gateway</span>
            <span className="font-semibold text-cyber-text capitalize">{gateway}</span>
          </div>
          <div className="flex justify-between border-b border-cyber-border pb-3 text-xs">
            <span className="text-cyber-muted">Error Code</span>
            <span className="font-mono text-cyber-red font-semibold">{code}</span>
          </div>
          <div className="flex justify-between border-b border-cyber-border pb-3 text-xs">
            <span className="text-cyber-muted">Transaction Ref</span>
            <span className="font-mono text-cyber-muted truncate max-w-[200px]">{txn}</span>
          </div>
          <p className="text-xs text-cyber-muted leading-relaxed pt-2">
            {userFriendlyExplanation}
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="btn-outline-cyber flex-1 py-3 text-xs font-semibold flex items-center justify-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
          </button>
          <button
            onClick={() => router.push("/dashboard/settings")}
            className="btn-cyber flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Payment
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BillingFailurePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <FailureContent />
    </Suspense>
  );
}
