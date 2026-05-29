"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Shield,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Check,
  X,
} from "lucide-react";

/* ── Password strength helper ──────────────────────────────── */
function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { score, label: "Very Weak", color: "#FF1744" };
  if (score === 2) return { score, label: "Weak", color: "#FF4757" };
  if (score === 3) return { score, label: "Fair", color: "#FF6B35" };
  if (score === 4) return { score, label: "Strong", color: "#2ED573" };
  return { score, label: "Very Strong", color: "#00D4FF" };
}

const passwordRequirements = [
  { label: "At least 8 characters", test: (p: string) => p.length >= 8 },
  { label: "One uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "One number", test: (p: string) => /[0-9]/.test(p) },
  {
    label: "One special character",
    test: (p: string) => /[^A-Za-z0-9]/.test(p),
  },
];

export default function ResetPasswordPage() {
  const [form, setForm] = useState({
    password: "",
    confirmPassword: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState(false);
  // Simulate token invalid — set to true to test error state
  const [tokenInvalid] = useState(false);

  const strength = getPasswordStrength(form.password);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!form.password) newErrors.password = "Password is required.";
    else if (form.password.length < 8)
      newErrors.password = "Password must be at least 8 characters.";
    if (!form.confirmPassword)
      newErrors.confirmPassword = "Please confirm your new password.";
    else if (form.password !== form.confirmPassword)
      newErrors.confirmPassword = "Passwords do not match.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    if (!validate()) return;
    setLoading(true);

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token") || "";

    if (!token) {
      setErrors({ password: "Reset token is missing from URL." });
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/reset-password/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password: form.password,
          confirm_password: form.confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.error || data.detail || "Resetting password failed.";
        setErrors({ password: errorMsg });
        setLoading(false);
        return;
      }

      setLoading(false);
      setSuccess(true);
    } catch (err) {
      setErrors({ password: "Could not connect to the auth server. Make sure the backend is running." });
      setLoading(false);
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: "" }));
  }

  /* ── Invalid token state ─────────────────────────────────── */
  if (tokenInvalid) {
    return (
      <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md text-center animate-fade-in-up">
          <div className="cyber-card p-8 shadow-cyber">
            <div className="w-16 h-16 mx-auto mb-5 bg-cyber-red/10 rounded-full flex items-center justify-center border border-cyber-red/30">
              <AlertCircle className="w-8 h-8 text-cyber-red" />
            </div>
            <h1 className="text-2xl font-bold text-cyber-text mb-2">
              Link Invalid or Expired
            </h1>
            <p className="text-cyber-muted text-sm mb-6 leading-relaxed">
              This password reset link is no longer valid. Reset links expire
              after 1 hour. Please request a new one.
            </p>
            <Link
              href="/auth/forgot-password"
              className="btn-cyber inline-flex items-center justify-center gap-2 w-full py-3.5 text-sm font-bold mb-3"
            >
              Request New Reset Link <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/auth/login"
              className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
            >
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

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
          {success ? (
            /* ── Success State ─────────────────────────────── */
            <div className="text-center py-4 animate-fade-in">
              <div className="w-20 h-20 mx-auto mb-5 relative">
                <div className="absolute inset-0 bg-cyber-green/10 rounded-full border border-cyber-green/30 animate-ping-slow" />
                <div className="relative w-full h-full bg-cyber-green/10 rounded-full border border-cyber-green/30 flex items-center justify-center">
                  <CheckCircle2 className="w-10 h-10 text-cyber-green" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-cyber-text mb-2">
                Password Reset!
              </h2>
              <p className="text-cyber-muted text-sm mb-6 leading-relaxed">
                Your password has been updated successfully. You can now sign in
                with your new password.
              </p>

              {/* Security tip */}
              <div className="bg-cyber-card/50 border border-cyber-border rounded-lg p-4 text-left mb-6">
                <p className="text-xs text-cyber-cyan font-medium mb-2 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  Security Recommendations
                </p>
                <ul className="space-y-1.5">
                  {[
                    "Enable two-factor authentication",
                    "Don't reuse this password elsewhere",
                    "Use a password manager",
                  ].map((tip) => (
                    <li key={tip} className="flex items-center gap-2 text-xs text-cyber-muted">
                      <Check className="w-3 h-3 text-cyber-green flex-shrink-0" />
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href="/auth/login"
                id="reset-go-login-btn"
                className="btn-cyber inline-flex items-center justify-center gap-2 w-full py-3.5 text-sm font-bold"
              >
                Sign In Now <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            /* ── Reset Form ─────────────────────────────────── */
            <>
              {/* Icon + Heading */}
              <div className="text-center mb-7">
                <div className="w-14 h-14 mx-auto mb-4 bg-cyber-cyan/10 rounded-xl flex items-center justify-center border border-cyber-cyan/20">
                  <Lock className="w-7 h-7 text-cyber-cyan" />
                </div>
                <h1 className="text-2xl font-bold text-cyber-text mb-2">
                  Set new password
                </h1>
                <p className="text-cyber-muted text-sm">
                  Choose a strong password to protect your account.
                </p>
              </div>

              <form onSubmit={handleSubmit} noValidate className="space-y-5">
                {/* New Password */}
                <div>
                  <label
                    htmlFor="reset-password"
                    className="block text-sm font-medium text-cyber-text mb-1.5"
                  >
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                    <input
                      id="reset-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Enter new password"
                      className={`scan-input w-full pl-10 pr-11 py-3 text-sm ${
                        errors.password
                          ? "border-cyber-red/60 focus:border-cyber-red"
                          : ""
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-cyan transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Password Strength Bar */}
                  {form.password && (
                    <div className="mt-2">
                      <div className="flex gap-1 mb-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className="h-1 flex-1 rounded-full transition-all duration-300"
                            style={{
                              backgroundColor:
                                i <= strength.score
                                  ? strength.color
                                  : "#1E2A3A",
                            }}
                          />
                        ))}
                      </div>
                      <p
                        className="text-xs font-medium"
                        style={{ color: strength.color }}
                      >
                        {strength.label}
                      </p>
                    </div>
                  )}

                  {/* Requirements */}
                  {form.password && (
                    <ul className="mt-2 space-y-1">
                      {passwordRequirements.map((req) => {
                        const passed = req.test(form.password);
                        return (
                          <li
                            key={req.label}
                            className="flex items-center gap-1.5 text-xs"
                          >
                            {passed ? (
                              <Check className="w-3 h-3 text-cyber-green" />
                            ) : (
                              <X className="w-3 h-3 text-cyber-muted" />
                            )}
                            <span
                              className={
                                passed ? "text-cyber-green" : "text-cyber-muted"
                              }
                            >
                              {req.label}
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  )}

                  {errors.password && (
                    <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" />
                      {errors.password}
                    </p>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label
                    htmlFor="reset-confirm"
                    className="block text-sm font-medium text-cyber-text mb-1.5"
                  >
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                    <input
                      id="reset-confirm"
                      name="confirmPassword"
                      type={showConfirm ? "text" : "password"}
                      autoComplete="new-password"
                      value={form.confirmPassword}
                      onChange={handleChange}
                      placeholder="Re-enter new password"
                      className={`scan-input w-full pl-10 pr-11 py-3 text-sm ${
                        errors.confirmPassword
                          ? "border-cyber-red/60 focus:border-cyber-red"
                          : form.confirmPassword &&
                            form.password === form.confirmPassword
                          ? "border-cyber-green/40"
                          : ""
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-cyan transition-colors"
                      aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
                    >
                      {showConfirm ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                    {form.confirmPassword &&
                      form.password === form.confirmPassword && (
                        <CheckCircle2 className="absolute right-10 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-green" />
                      )}
                  </div>
                  {errors.confirmPassword && (
                    <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" />
                      {errors.confirmPassword}
                    </p>
                  )}
                </div>

                {/* Submit */}
                <button
                  id="reset-submit-btn"
                  type="submit"
                  disabled={loading}
                  className="btn-cyber w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold disabled:opacity-60 disabled:cursor-not-allowed mt-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Updating password...
                    </>
                  ) : (
                    <>
                      Reset Password <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-cyber-muted mt-6">
          Protected by WebGuard Pro security infrastructure.
          <br />
          Your data is encrypted end-to-end.
        </p>
      </div>
    </div>
  );
}
