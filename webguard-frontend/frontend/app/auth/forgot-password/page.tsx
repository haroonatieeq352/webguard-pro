"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Shield,
  Mail,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  KeyRound,
} from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  function validate(): boolean {
    if (!email.trim()) {
      setError("Email is required.");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Enter a valid email address.");
      return false;
    }
    return true;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!validate()) return;
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/forgot-password/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.error || data.detail || "Request failed.";
        setError(errorMsg);
        setLoading(false);
        return;
      }

      setLoading(false);
      setSubmitted(true);
    } catch (err) {
      setError("Could not connect to the auth server. Make sure the backend is running.");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 right-1/3 w-80 h-80 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/3 left-1/4 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

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
        <div className="cyber-card p-8 shadow-cyber">
          {!submitted ? (
            /* ── Request Form ──────────────────────────────── */
            <>
              {/* Icon + Heading */}
              <div className="text-center mb-7">
                <div className="w-14 h-14 mx-auto mb-4 bg-cyber-cyan/10 rounded-xl flex items-center justify-center border border-cyber-cyan/20">
                  <KeyRound className="w-7 h-7 text-cyber-cyan" />
                </div>
                <h1 className="text-2xl font-bold text-cyber-text mb-2">
                  Forgot your password?
                </h1>
                <p className="text-cyber-muted text-sm leading-relaxed">
                  No worries — enter your email and we&apos;ll send you a secure
                  reset link. Link expires in{" "}
                  <span className="text-cyber-cyan font-medium">1 hour</span>.
                </p>
              </div>

              <form onSubmit={handleSubmit} noValidate className="space-y-5">
                {/* Email Input */}
                <div>
                  <label
                    htmlFor="forgot-email"
                    className="block text-sm font-medium text-cyber-text mb-1.5"
                  >
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                    <input
                      id="forgot-email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setError("");
                      }}
                      placeholder="haroon@example.com"
                      className={`scan-input w-full pl-10 pr-4 py-3 text-sm ${
                        error
                          ? "border-cyber-red/60 focus:border-cyber-red"
                          : ""
                      }`}
                    />
                  </div>
                  {error && (
                    <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" />
                      {error}
                    </p>
                  )}
                </div>

                {/* Security note */}
                <div className="bg-cyber-card/50 border border-cyber-border rounded-lg p-3.5 text-xs text-cyber-muted leading-relaxed">
                  <p className="font-medium text-cyber-text mb-1">🔒 Security Note</p>
                  For your security, we send reset links even if the email
                  isn&apos;t registered — this prevents account enumeration.
                </div>

                {/* Submit */}
                <button
                  id="forgot-submit-btn"
                  type="submit"
                  disabled={loading}
                  className="btn-cyber w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending reset link...
                    </>
                  ) : (
                    <>
                      Send Reset Link <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

                {/* Back to login */}
                <Link
                  href="/auth/login"
                  className="flex items-center justify-center gap-1.5 text-sm text-cyber-muted hover:text-cyber-cyan transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Login
                </Link>
              </form>
            </>
          ) : (
            /* ── Success State ─────────────────────────────── */
            <div className="text-center py-4 animate-fade-in">
              {/* Animated envelope */}
              <div className="w-20 h-20 mx-auto mb-5 relative">
                <div className="absolute inset-0 bg-cyber-cyan/10 rounded-full border border-cyber-cyan/20 animate-ping-slow" />
                <div className="relative w-full h-full bg-cyber-cyan/10 rounded-full border border-cyber-cyan/20 flex items-center justify-center">
                  <Mail className="w-9 h-9 text-cyber-cyan" />
                </div>
              </div>

              <h2 className="text-2xl font-bold text-cyber-text mb-2">
                Check your inbox!
              </h2>
              <p className="text-cyber-muted text-sm mb-2 leading-relaxed">
                We&apos;ve sent a password reset link to:
              </p>
              <p className="text-cyber-cyan font-semibold text-sm mb-6 bg-cyber-cyan/5 border border-cyber-cyan/20 rounded-lg px-4 py-2.5 inline-block">
                {email}
              </p>

              {/* Checklist */}
              <div className="bg-cyber-card/50 border border-cyber-border rounded-lg p-4 text-left mb-6 space-y-2">
                {[
                  "Check your email inbox",
                  "Click the reset link in the email",
                  "Link expires in 1 hour",
                  "Check spam/junk if not found",
                ].map((step, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-cyber-muted">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyber-cyan flex-shrink-0" />
                    {step}
                  </div>
                ))}
              </div>

              <Link
                href="/auth/login"
                className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
                id="forgot-back-login-btn"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          )}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-cyber-muted mt-6">
          Still having trouble?{" "}
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
