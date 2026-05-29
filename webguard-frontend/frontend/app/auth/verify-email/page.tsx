"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Shield,
  Mail,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  ArrowRight,
} from "lucide-react";

type VerifyState = "verifying" | "success" | "expired" | "invalid";

export default function EmailVerifyPage() {
  const [state, setState] = useState<VerifyState>("verifying");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Verify token on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (!token) {
      setState("invalid");
      return;
    }

    async function verify() {
      try {
        const response = await fetch("http://localhost:8000/api/v1/auth/verify-email/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          setState("success");
        } else {
          const data = await response.json();
          const errorMsg = data.error || "";
          if (errorMsg.includes("expired")) {
            setState("expired");
          } else {
            setState("invalid");
          }
        }
      } catch (err) {
        setState("invalid");
      }
    }

    verify();
  }, []);

  // Countdown timer for resend cooldown
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  async function handleResend() {
    if (resendCooldown > 0) return;
    setResendLoading(true);
    setResendSuccess(false);

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");
    let email = "";

    if (token) {
      const parts = token.split('.');
      if (parts.length === 3) {
        try {
          const decodedPayload = atob(parts[1]);
          const payload = JSON.parse(decodedPayload);
          email = payload.email;
        } catch (e) {
          console.error("Failed to decode token email", e);
        }
      }
    }

    if (!email) {
      setResendLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/resend-verification/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setResendSuccess(true);
        setResendCooldown(60);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 animate-fade-in-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6 group">
            <div className="relative">
              <Shield className="w-9 h-9 text-cyber-cyan group-hover:scale-110 transition-transform" />
              <div className="absolute inset-0 bg-cyber-cyan/20 rounded-full blur-md group-hover:bg-cyber-cyan/30 transition-all" />
            </div>
            <span className="text-xl font-bold gradient-text-cyan">
              WebGuard Pro
            </span>
          </Link>
        </div>

        {/* Card */}
        <div className="cyber-card p-8 shadow-cyber text-center">

          {/* ── Verifying State ─────────────────────────── */}
          {state === "verifying" && (
            <div className="py-6 animate-fade-in">
              <div className="w-16 h-16 mx-auto mb-5 bg-cyber-cyan/10 rounded-full flex items-center justify-center border border-cyber-cyan/20 scan-line-anim">
                <Loader2 className="w-8 h-8 text-cyber-cyan animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-cyber-text mb-2">
                Verifying your email...
              </h1>
              <p className="text-cyber-muted text-sm">
                Please wait while we validate your verification link.
              </p>
            </div>
          )}

          {/* ── Success State ───────────────────────────── */}
          {state === "success" && (
            <div className="py-4 animate-fade-in">
              {/* Animated checkmark */}
              <div className="w-20 h-20 mx-auto mb-5 relative">
                <div className="absolute inset-0 bg-cyber-green/10 rounded-full border border-cyber-green/30 animate-ping-slow" />
                <div className="relative w-full h-full bg-cyber-green/10 rounded-full border border-cyber-green/30 flex items-center justify-center">
                  <CheckCircle2 className="w-10 h-10 text-cyber-green" />
                </div>
              </div>
              <h1 className="text-2xl font-bold text-cyber-text mb-2">
                Email Verified!
              </h1>
              <p className="text-cyber-muted text-sm mb-6 leading-relaxed">
                Your account is now active. You can sign in and start scanning
                your websites for vulnerabilities.
              </p>

              {/* Security shield detail */}
              <div className="bg-cyber-green/5 border border-cyber-green/20 rounded-lg p-4 mb-6 text-left">
                <p className="text-xs text-cyber-green font-medium mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Account Security Active
                </p>
                <p className="text-xs text-cyber-muted">
                  Two-factor authentication is available in your account settings.
                </p>
              </div>

              <Link
                href="/auth/login"
                className="btn-cyber inline-flex items-center justify-center gap-2 w-full py-3.5 text-sm font-bold"
                id="verify-go-to-login-btn"
              >
                Go to Login <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}

          {/* ── Expired Token State ─────────────────────── */}
          {state === "expired" && (
            <div className="py-4 animate-fade-in">
              <div className="w-16 h-16 mx-auto mb-5 bg-cyber-orange/10 rounded-full flex items-center justify-center border border-cyber-orange/30">
                <Mail className="w-8 h-8 text-cyber-orange" />
              </div>
              <h1 className="text-2xl font-bold text-cyber-text mb-2">
                Link Expired
              </h1>
              <p className="text-cyber-muted text-sm mb-6 leading-relaxed">
                Your verification link has expired (valid for 24 hours). 
                Request a new one and check your inbox.
              </p>

              {resendSuccess && (
                <div className="mb-4 p-3 bg-cyber-green/10 border border-cyber-green/20 rounded-lg flex items-center gap-2 text-left">
                  <CheckCircle2 className="w-4 h-4 text-cyber-green flex-shrink-0" />
                  <p className="text-xs text-cyber-green">
                    New verification email sent! Check your inbox.
                  </p>
                </div>
              )}

              <button
                id="verify-resend-btn"
                onClick={handleResend}
                disabled={resendLoading || resendCooldown > 0}
                className="btn-cyber w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold disabled:opacity-60 disabled:cursor-not-allowed mb-3"
              >
                {resendLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending...
                  </>
                ) : resendCooldown > 0 ? (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Resend in {resendCooldown}s
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Resend Verification Email
                  </>
                )}
              </button>

              <Link
                href="/auth/login"
                className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
              >
                Back to Login
              </Link>
            </div>
          )}

          {/* ── Invalid Token State ─────────────────────── */}
          {state === "invalid" && (
            <div className="py-4 animate-fade-in">
              <div className="w-16 h-16 mx-auto mb-5 bg-cyber-red/10 rounded-full flex items-center justify-center border border-cyber-red/30">
                <XCircle className="w-8 h-8 text-cyber-red" />
              </div>
              <h1 className="text-2xl font-bold text-cyber-text mb-2">
                Invalid Link
              </h1>
              <p className="text-cyber-muted text-sm mb-6 leading-relaxed">
                This verification link is invalid or has already been used.
                Please register again or contact support.
              </p>

              <Link
                href="/auth/register"
                className="btn-cyber inline-flex items-center justify-center gap-2 w-full py-3.5 text-sm font-bold mb-3"
              >
                Create New Account
              </Link>
              <Link
                href="/auth/login"
                className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
              >
                Back to Login
              </Link>
            </div>
          )}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-cyber-muted mt-6">
          Didn&apos;t receive an email? Check your spam folder.
          <br />
          Need help?{" "}
          <Link
            href="mailto:support@webguardpro.io"
            className="text-cyber-cyan hover:underline"
          >
            Contact support
          </Link>
        </p>
      </div>
    </div>
  );
}
