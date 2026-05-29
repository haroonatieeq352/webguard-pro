"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Eye,
  EyeOff,
  Shield,
  Mail,
  Lock,
  User,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Loader2,
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

/* ── Component ─────────────────────────────────────────────── */
export default function RegisterPage() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    terms: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [success, setSuccess] = useState(false);

  const strength = getPasswordStrength(form.password);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!form.name.trim()) newErrors.name = "Full name is required.";
    if (!form.email.trim()) newErrors.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      newErrors.email = "Enter a valid email address.";
    if (!form.password) newErrors.password = "Password is required.";
    else if (form.password.length < 8)
      newErrors.password = "Password must be at least 8 characters.";
    if (!form.confirmPassword)
      newErrors.confirmPassword = "Please confirm your password.";
    else if (form.password !== form.confirmPassword)
      newErrors.confirmPassword = "Passwords do not match.";
    if (!form.terms)
      newErrors.terms = "You must accept the Terms of Service.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: form.email.toLowerCase().trim(),
          full_name: form.name.trim(),
          password: form.password,
          confirm_password: form.confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Show validation or registration error from Django backend
        let errorMsg = data.error || data.detail || "Registration failed.";
        if (data.details && typeof data.details === "object") {
          // If detailed errors are returned, extract first message
          const firstKey = Object.keys(data.details)[0];
          const firstErr = data.details[firstKey];
          errorMsg = Array.isArray(firstErr) ? firstErr[0] : String(firstErr);
        }
        setApiError(errorMsg);
        setLoading(false);
        return;
      }

      setLoading(false);
      setSuccess(true);
    } catch (err) {
      setApiError("Could not connect to the auth server. Make sure the backend is running.");
      setLoading(false);
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: "" }));
  }

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 animate-fade-in-up">
        {/* Logo + Heading */}
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
          <h1 className="text-3xl font-extrabold text-cyber-text mb-2">
            Create your account
          </h1>
          <p className="text-cyber-muted text-sm">
            Start scanning for free — no credit card required
          </p>
        </div>

        {/* Card */}
        <div className="cyber-card p-8 shadow-cyber">
          {success ? (
            /* ── Success State ─────────────────────────────── */
            <div className="text-center py-6 animate-fade-in">
              <div className="w-16 h-16 mx-auto mb-4 bg-cyber-green/10 rounded-full flex items-center justify-center border border-cyber-green/30">
                <CheckCircle2 className="w-8 h-8 text-cyber-green" />
              </div>
              <h2 className="text-xl font-bold text-cyber-text mb-2">
                Account Created!
              </h2>
              <p className="text-cyber-muted text-sm mb-6">
                We&apos;ve sent a verification email to{" "}
                <span className="text-cyber-cyan font-medium">{form.email}</span>
                . Check your inbox and verify your account to get started.
              </p>
              <Link
                href="/auth/login"
                className="btn-cyber inline-flex items-center gap-2 px-6 py-3 text-sm font-bold"
              >
                Go to Login <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            /* ── Register Form ─────────────────────────────── */
            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              {/* API Error Banner */}
              {apiError && (
                <div className="mb-5 p-3.5 bg-cyber-red/10 border border-cyber-red/30 rounded-lg flex items-start gap-3 animate-fade-in">
                  <AlertCircle className="w-4 h-4 text-cyber-red mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-cyber-red">{apiError}</p>
                </div>
              )}
              {/* Full Name */}
              <div>
                <label
                  htmlFor="register-name"
                  className="block text-sm font-medium text-cyber-text mb-1.5"
                >
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                  <input
                    id="register-name"
                    name="name"
                    type="text"
                    autoComplete="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Haroon Atieeque"
                    className={`scan-input w-full pl-10 pr-4 py-3 text-sm ${
                      errors.name
                        ? "border-cyber-red/60 focus:border-cyber-red"
                        : ""
                    }`}
                  />
                </div>
                {errors.name && (
                  <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {errors.name}
                  </p>
                )}
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="register-email"
                  className="block text-sm font-medium text-cyber-text mb-1.5"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                  <input
                    id="register-email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="haroon@example.com"
                    className={`scan-input w-full pl-10 pr-4 py-3 text-sm ${
                      errors.email
                        ? "border-cyber-red/60 focus:border-cyber-red"
                        : ""
                    }`}
                  />
                </div>
                {errors.email && (
                  <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {errors.email}
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="register-password"
                  className="block text-sm font-medium text-cyber-text mb-1.5"
                >
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                  <input
                    id="register-password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={form.password}
                    onChange={handleChange}
                    placeholder="Create a strong password"
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

                {/* Password Requirements */}
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
                  htmlFor="register-confirm"
                  className="block text-sm font-medium text-cyber-text mb-1.5"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                  <input
                    id="register-confirm"
                    name="confirmPassword"
                    type={showConfirm ? "text" : "password"}
                    autoComplete="new-password"
                    value={form.confirmPassword}
                    onChange={handleChange}
                    placeholder="Re-enter your password"
                    className={`scan-input w-full pl-10 pr-11 py-3 text-sm ${
                      errors.confirmPassword
                        ? "border-cyber-red/60 focus:border-cyber-red"
                        : form.confirmPassword && form.password === form.confirmPassword
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

              {/* Terms checkbox */}
              <div>
                <label
                  htmlFor="register-terms"
                  className="flex items-start gap-3 cursor-pointer group"
                >
                  <div className="relative mt-0.5">
                    <input
                      id="register-terms"
                      name="terms"
                      type="checkbox"
                      checked={form.terms}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <div
                      className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${
                        form.terms
                          ? "bg-cyber-cyan border-cyber-cyan"
                          : "bg-transparent border-cyber-border group-hover:border-cyber-cyan/50"
                      } ${errors.terms ? "border-cyber-red" : ""}`}
                    >
                      {form.terms && <Check className="w-3 h-3 text-cyber-bg" />}
                    </div>
                  </div>
                  <span className="text-sm text-cyber-muted leading-tight">
                    I agree to the{" "}
                    <Link
                      href="/terms"
                      className="text-cyber-cyan hover:underline"
                    >
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link
                      href="/privacy"
                      className="text-cyber-cyan hover:underline"
                    >
                      Privacy Policy
                    </Link>
                  </span>
                </label>
                {errors.terms && (
                  <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {errors.terms}
                  </p>
                )}
              </div>

              {/* Submit Button */}
              <button
                id="register-submit-btn"
                type="submit"
                disabled={loading}
                className="btn-cyber w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold disabled:opacity-60 disabled:cursor-not-allowed mt-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Create Account <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              {/* Divider */}
              <div className="relative my-1">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-cyber-border" />
                </div>
                <div className="relative flex justify-center text-xs text-cyber-muted bg-cyber-card px-3">
                  already have an account?
                </div>
              </div>

              {/* Login Link */}
              <Link
                href="/auth/login"
                className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
              >
                Sign In Instead
              </Link>
            </form>
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
