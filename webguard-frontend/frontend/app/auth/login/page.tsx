"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye,
  EyeOff,
  Shield,
  Mail,
  Lock,
  AlertCircle,
  ArrowRight,
  Loader2,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");

  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!form.email.trim()) newErrors.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      newErrors.email = "Enter a valid email address.";
    if (!form.password) newErrors.password = "Password is required.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/token/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: form.email.toLowerCase().trim(),
          password: form.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Show validation or auth error from DRF
        const errorMsg = data.message || data.detail || data.error || "Invalid email or password.";
        setApiError(errorMsg);
        setLoading(false);
        return;
      }

      // Success: Save tokens and user info to localStorage
      localStorage.setItem("wg-token", data.access);
      localStorage.setItem("wg-refresh-token", data.refresh);
      localStorage.setItem("wg-user", JSON.stringify(data.user));

      setLoading(false);
      router.push("/dashboard");
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
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

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
            Welcome back
          </h1>
          <p className="text-cyber-muted text-sm">
            Sign in to access your security dashboard
          </p>
        </div>

        {/* Card */}
        <div className="cyber-card p-8 shadow-cyber">
          {/* API Error Banner */}
          {apiError && (
            <div className="mb-5 p-3.5 bg-cyber-red/10 border border-cyber-red/30 rounded-lg flex items-start gap-3 animate-fade-in">
              <AlertCircle className="w-4 h-4 text-cyber-red mt-0.5 flex-shrink-0" />
              <p className="text-sm text-cyber-red">{apiError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Email */}
            <div>
              <label
                htmlFor="login-email"
                className="block text-sm font-medium text-cyber-text mb-1.5"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                <input
                  id="login-email"
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
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="login-password"
                  className="block text-sm font-medium text-cyber-text"
                >
                  Password
                </label>
                <Link
                  href="/auth/forgot-password"
                  className="text-xs text-cyber-cyan hover:text-cyber-cyan/80 hover:underline transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
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
              {errors.password && (
                <p className="mt-1.5 text-xs text-cyber-red flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  {errors.password}
                </p>
              )}
            </div>

            {/* Remember Me */}
            <label
              htmlFor="login-remember"
              className="flex items-center gap-3 cursor-pointer group w-fit"
            >
              <div className="relative">
                <input
                  id="login-remember"
                  name="rememberMe"
                  type="checkbox"
                  checked={form.rememberMe}
                  onChange={handleChange}
                  className="sr-only"
                />
                <div
                  className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${
                    form.rememberMe
                      ? "bg-cyber-cyan border-cyber-cyan"
                      : "bg-transparent border-cyber-border group-hover:border-cyber-cyan/50"
                  }`}
                >
                  {form.rememberMe && (
                    <svg className="w-3 h-3 text-cyber-bg" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              </div>
              <span className="text-sm text-cyber-muted group-hover:text-cyber-text transition-colors">
                Remember me for 30 days
              </span>
            </label>

            {/* Submit Button */}
            <button
              id="login-submit-btn"
              type="submit"
              disabled={loading}
              className="btn-cyber w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Brute force notice */}
            <p className="text-center text-xs text-cyber-muted">
              Account locks for 15 min after 5 failed attempts.
            </p>

            {/* Divider */}
            <div className="relative my-1">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-cyber-border" />
              </div>
              <div className="relative flex justify-center text-xs text-cyber-muted bg-cyber-card px-3">
                don&apos;t have an account?
              </div>
            </div>

            {/* Register Link */}
            <Link
              href="/auth/register"
              className="btn-outline-cyber w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold"
            >
              Create Free Account
            </Link>
          </form>
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
