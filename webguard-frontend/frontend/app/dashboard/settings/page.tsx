"use client";

import { useState, useEffect } from "react";
import {
  User, Mail, Lock, Key, CreditCard, Eye, EyeOff,
  Copy, RefreshCw, Check, AlertCircle, Loader2,
  Crown, Zap, Shield, ArrowRight, Trash2, CheckCircle2,
} from "lucide-react";
import { apiPost, apiGet, apiPut } from "../../../lib/api";

/* ── Mock data ───────────────────────────────────────────── */
const mockApiKeys = [
  { id: "k1", name: "Production Key",   key: "wg_live_Xk9mN3pR7qY2wZ8vL4jK1nM6",  created: "2026-05-01", lastUsed: "2 hrs ago" },
  { id: "k2", name: "CI/CD Integration", key: "wg_live_Bx3cT5uP9sA1dF0eH7gQ2nR4",  created: "2026-05-15", lastUsed: "Yesterday" },
];

const plans = [
  { id: "free",       label: "Free",       price: "$0",   color: "#94A3B8", icon: null,   features: ["3 scans/month", "Quick scan only", "5 AI messages/scan"] },
  { id: "pro",        label: "Pro",        price: "$9",   color: "#00D4FF", icon: Zap,    features: ["Unlimited scans", "DAST engine", "AI Security Advisor", "PDF reports"], current: true },
  { id: "business",   label: "Business",   price: "$19",  color: "#A78BFA", icon: Crown,  features: ["Everything in Pro", "Business checks", "Subdomain enum", "Priority support"] },
  { id: "enterprise", label: "Enterprise", price: "$49",  color: "#FFD60A", icon: Crown,  features: ["Everything in Business", "Custom AI persona", "SLA", "White-label"] },
];

/* ── Section wrapper ─────────────────────────────────────── */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="cyber-card p-6 space-y-5">
      <h3 className="text-sm font-semibold text-cyber-muted uppercase tracking-wider border-b border-cyber-border pb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

/* ── Input field ─────────────────────────────────────────── */
function Field({
  id, label, type = "text", value, onChange, icon: Icon, placeholder, readOnly,
}: {
  id: string; label: string; type?: string; value: string;
  onChange?: (v: string) => void; icon: React.ElementType;
  placeholder?: string; readOnly?: boolean;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-cyber-text mb-1.5">{label}</label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
        <input
          id={id} type={type} value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder={placeholder}
          readOnly={readOnly}
          className={`scan-input w-full pl-10 pr-4 py-3 text-sm ${readOnly ? "opacity-60 cursor-not-allowed" : ""}`}
        />
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────── */
export default function SettingsPage() {
  // Profile
  const [name, setName]   = useState("");
  const [email, setEmail] = useState("");
  const [initials, setInitials] = useState("");
  const [userPlan, setUserPlan] = useState("free");
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);

  // Password
  const [currentPw, setCurrentPw]   = useState("");
  const [newPw, setNewPw]           = useState("");
  const [confirmPw, setConfirmPw]   = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw]         = useState(false);
  const [pwError, setPwError]             = useState("");
  const [pwSaved, setPwSaved]             = useState(false);
  const [pwLoading, setPwLoading]         = useState(false);

  // API key
  const [apiKey, setApiKey]     = useState<string | null>(null);
  const [copied, setCopied]     = useState(false);
  const [genLoading, setGenLoading] = useState(false);

  // Billing portal
  const [billingLoading, setBillingLoading] = useState(false);

  // Checkout Modal
  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);
  const [selectedTier, setSelectedTier]           = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod]         = useState("stripe"); // 'stripe' | 'jazzcash' | 'easypaisa'
  const [mobileNo, setMobileNo]                   = useState("");
  const [checkoutLoading, setCheckoutLoading]     = useState(false);
  const [checkoutError, setCheckoutError]         = useState("");
  const [easypaisaSuccess, setEasypaisaSuccess]   = useState(false);

  async function handleCheckoutSubmit() {
    if (!selectedTier) return;
    setCheckoutLoading(true);
    setCheckoutError("");

    try {
      if (paymentMethod === "stripe") {
        const res = await apiPost("billing/stripe/checkout/", {
          tier: selectedTier,
          interval: "monthly",
        });
        const data = await res.json();
        if (res.ok && data.checkout_url) {
          window.location.href = data.checkout_url;
        } else {
          setCheckoutError(data.error || "Failed to initiate Stripe payment.");
        }
      } else if (paymentMethod === "jazzcash") {
        const res = await apiPost("billing/jazzcash/initiate/", {
          tier: selectedTier,
        });
        const data = await res.json();
        if (res.ok) {
          // Submit hidden form to simulate or redirect to JazzCash sandbox/mock callback
          if (data.is_mock && data.mock_callback_url) {
            const form = document.createElement("form");
            form.method = "POST";
            form.action = data.mock_callback_url;
            
            Object.keys(data.fields).forEach((key) => {
              const input = document.createElement("input");
              input.type = "hidden";
              input.name = key;
              input.value = data.fields[key];
              form.appendChild(input);
            });
            
            document.body.appendChild(form);
            form.submit();
          } else {
            const form = document.createElement("form");
            form.method = "POST";
            form.action = data.api_url;
            
            Object.keys(data.fields).forEach((key) => {
              const input = document.createElement("input");
              input.type = "hidden";
              input.name = key;
              input.value = data.fields[key];
              form.appendChild(input);
            });
            
            document.body.appendChild(form);
            form.submit();
          }
        } else {
          setCheckoutError(data.error || "Failed to initiate JazzCash payment.");
        }
      } else if (paymentMethod === "easypaisa") {
        if (!mobileNo.trim() || mobileNo.length < 11) {
          setCheckoutError("Please enter a valid 11-digit EasyPaisa mobile number.");
          setCheckoutLoading(false);
          return;
        }
        const res = await apiPost("billing/easypaisa/initiate/", {
          tier: selectedTier,
          mobile_no: mobileNo,
        });
        const data = await res.json();
        if (res.ok) {
          setEasypaisaSuccess(true);
        } else {
          setCheckoutError(data.error || "Failed to initiate EasyPaisa payment.");
        }
      }
    } catch (err) {
      setCheckoutError("Payment gateway connection failed. Make sure the backend is online.");
    } finally {
      setCheckoutLoading(false);
    }
  }

  async function handleManageBilling() {
    setBillingLoading(true);
    try {
      const res = await apiPost("billing/stripe/portal/");
      const data = await res.json();
      if (res.ok && data.portal_url) {
        window.location.href = data.portal_url;
      } else {
        alert(data.error || "Billing portal access is only available for active Stripe subscribers.");
      }
    } catch (err) {
      alert("Failed to connect to billing portal service.");
    } finally {
      setBillingLoading(false);
    }
  }

  useEffect(() => {
    // 1. Initial load from localStorage for speed
    const rawUser = localStorage.getItem("wg-user");
    if (rawUser) {
      try {
        const u = JSON.parse(rawUser);
        const fullName = u.full_name || u.email.split("@")[0];
        setName(fullName);
        setEmail(u.email);
        setUserPlan(u.subscription_tier || "free");
        setApiKey(u.api_key || null);
        const userInitials = fullName
          .split(" ")
          .map((n: string) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2) || "U";
        setInitials(userInitials);
      } catch (e) {
        console.error("Failed to parse user", e);
      }
    }

    // 2. Fetch fresh user details from backend
    async function fetchMe() {
      try {
        const res = await apiGet("auth/me/");
        if (res.ok) {
          const data = await res.json();
          setName(data.full_name || "");
          setEmail(data.email || "");
          setUserPlan(data.subscription_tier || "free");
          setApiKey(data.api_key || null);
          const fullName = data.full_name || data.email.split("@")[0];
          const userInitials = fullName
            .split(" ")
            .map((n: string) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2) || "U";
          setInitials(userInitials);
          // Sync localStorage
          localStorage.setItem("wg-user", JSON.stringify(data));
        }
      } catch (err) {
        console.error("Failed to fetch fresh user details", err);
      }
    }
    fetchMe();
  }, []);

  /* Profile save */
  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileLoading(true);
    try {
      const res = await apiPut("auth/profile/", { full_name: name });
      if (res.ok) {
        const data = await res.json();
        setName(data.full_name || name);
        // Sync local storage
        const rawUser = localStorage.getItem("wg-user");
        if (rawUser) {
          const u = JSON.parse(rawUser);
          u.full_name = data.full_name || name;
          localStorage.setItem("wg-user", JSON.stringify(u));
        }
        // Compute new initials
        const fullName = data.full_name || name;
        const userInitials = fullName
          .split(" ")
          .map((n: string) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2) || "U";
        setInitials(userInitials);
        setProfileSaved(true);
        setTimeout(() => setProfileSaved(false), 3000);
      } else {
        alert("Failed to update profile details.");
      }
    } catch (err) {
      alert("Failed to connect to profile service.");
    } finally {
      setProfileLoading(false);
    }
  }

  /* Password change */
  async function savePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwError("");
    if (!currentPw) { setPwError("Current password is required."); return; }
    if (newPw.length < 8) { setPwError("New password must be at least 8 characters."); return; }
    if (newPw !== confirmPw) { setPwError("Passwords do not match."); return; }
    setPwLoading(true);
    try {
      const res = await apiPost("auth/change-password/", {
        current_password: currentPw,
        new_password: newPw,
        confirm_new_password: confirmPw,
      });
      const data = await res.json();
      if (!res.ok) {
        setPwError(data.error || (data.details && Object.values(data.details).join(" ")) || "Failed to update password.");
        return;
      }
      setPwSaved(true);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      setTimeout(() => setPwSaved(false), 3000);
    } catch (err) {
      setPwError("Failed to connect to password update service.");
    } finally {
      setPwLoading(false);
    }
  }

  /* Copy API key */
  async function copyKey() {
    if (!apiKey) return;
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  /* Generate new key */
  async function generateKey() {
    setGenLoading(true);
    try {
      const res = await apiPost("auth/apikey/generate/");
      if (res.ok) {
        const data = await res.json();
        setApiKey(data.api_key);
        // Sync local storage
        const rawUser = localStorage.getItem("wg-user");
        if (rawUser) {
          const u = JSON.parse(rawUser);
          u.api_key = data.api_key;
          localStorage.setItem("wg-user", JSON.stringify(u));
        }
      } else {
        alert("Failed to generate API Key.");
      }
    } catch (err) {
      alert("Failed to connect to API key service.");
    } finally {
      setGenLoading(false);
    }
  }

  /* Revoke key */
  async function revokeKey() {
    if (!confirm("Are you sure you want to revoke this API key? Any applications using it will be blocked immediately.")) return;
    try {
      const res = await apiPost("auth/apikey/revoke/");
      if (res.ok) {
        setApiKey(null);
        // Sync local storage
        const rawUser = localStorage.getItem("wg-user");
        if (rawUser) {
          const u = JSON.parse(rawUser);
          u.api_key = null;
          localStorage.setItem("wg-user", JSON.stringify(u));
        }
      } else {
        alert("Failed to revoke API Key.");
      }
    } catch (err) {
      alert("Failed to connect to API key service.");
    }
  }

  const isProOrHigher = userPlan === "pro" || userPlan === "business" || userPlan === "enterprise";

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-cyber-text">Settings</h2>
        <p className="text-sm text-cyber-muted">Manage your account, security, and preferences.</p>
      </div>

      {/* ── Profile ────────────────────────────────────────── */}
      <Section title="Profile">
        <form onSubmit={saveProfile} className="space-y-4">
          {/* Avatar */}
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyber-cyan to-purple-500 flex items-center justify-center text-cyber-bg text-xl font-bold flex-shrink-0">
              {initials || "U"}
            </div>
            <div>
              <p className="text-sm font-semibold text-cyber-text">Profile Photo</p>
              <p className="text-xs text-cyber-muted mb-2">Avatar auto-generated from initials</p>
              <button type="button" className="btn-outline-cyber px-3 py-1.5 text-xs font-medium">
                Upload Photo
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field id="settings-name"  label="Full Name"     value={name}  onChange={setName} icon={User} placeholder="Your full name" />
            <Field id="settings-email" label="Email Address" value={email} icon={Mail} readOnly />
          </div>
          <div className="flex items-center gap-3">
            <button
              id="settings-save-profile-btn"
              type="submit"
              disabled={profileLoading}
              className="btn-cyber px-5 py-2.5 text-sm font-bold flex items-center gap-2 disabled:opacity-60"
            >
              {profileLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</> : "Save Changes"}
            </button>
            {profileSaved && (
              <span className="flex items-center gap-1.5 text-sm text-cyber-green animate-fade-in">
                <CheckCircle2 className="w-4 h-4" /> Saved!
              </span>
            )}
          </div>
        </form>
      </Section>

      {/* ── Security ───────────────────────────────────────── */}
      <Section title="Security — Change Password">
        <form onSubmit={savePassword} className="space-y-4">
          {/* Current password */}
          <div>
            <label htmlFor="settings-current-pw" className="block text-sm font-medium text-cyber-text mb-1.5">
              Current Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
              <input
                id="settings-current-pw"
                type={showCurrentPw ? "text" : "password"}
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                placeholder="Enter current password"
                className="scan-input w-full pl-10 pr-11 py-3 text-sm"
              />
              <button type="button" onClick={() => setShowCurrentPw(!showCurrentPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-cyan">
                {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* New password */}
            <div>
              <label htmlFor="settings-new-pw" className="block text-sm font-medium text-cyber-text mb-1.5">
                New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                <input
                  id="settings-new-pw"
                  type={showNewPw ? "text" : "password"}
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  placeholder="New password"
                  className="scan-input w-full pl-10 pr-11 py-3 text-sm"
                />
                <button type="button" onClick={() => setShowNewPw(!showNewPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-cyan">
                  {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            {/* Confirm */}
            <div>
              <label htmlFor="settings-confirm-pw" className="block text-sm font-medium text-cyber-text mb-1.5">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
                <input
                  id="settings-confirm-pw" type="password" value={confirmPw}
                  onChange={(e) => setConfirmPw(e.target.value)}
                  placeholder="Confirm new password"
                  className={`scan-input w-full pl-10 pr-4 py-3 text-sm ${
                    confirmPw && newPw !== confirmPw ? "border-cyber-red/40" : confirmPw && newPw === confirmPw ? "border-cyber-green/40" : ""
                  }`}
                />
              </div>
            </div>
          </div>

          {pwError && (
            <p className="text-xs text-cyber-red flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" /> {pwError}
            </p>
          )}
          <div className="flex items-center gap-3">
            <button
              id="settings-save-pw-btn"
              type="submit"
              disabled={pwLoading}
              className="btn-cyber px-5 py-2.5 text-sm font-bold flex items-center gap-2 disabled:opacity-60"
            >
              {pwLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Updating...</> : "Update Password"}
            </button>
            {pwSaved && (
              <span className="flex items-center gap-1.5 text-sm text-cyber-green animate-fade-in">
                <CheckCircle2 className="w-4 h-4" /> Password updated!
              </span>
            )}
          </div>
        </form>
      </Section>

      {/* ── API Keys ───────────────────────────────────────── */}
      <Section title="API Keys">
        <p className="text-xs text-cyber-muted">
          Use API keys to integrate WebGuard Pro scans into your CI/CD pipeline.
        </p>
        
        {!isProOrHigher ? (
          <div className="p-4 bg-cyber-cyan/5 border border-cyber-cyan/20 rounded-xl space-y-3">
            <p className="text-xs text-cyber-muted leading-relaxed">
              API key access is an exclusive feature of our premium plans (Pro, Business, Enterprise) to automate security audits.
            </p>
            <button
              onClick={() => {
                setSelectedTier("pro");
                setCheckoutModalOpen(true);
              }}
              className="btn-cyber py-2 px-4 text-xs font-bold"
            >
              Upgrade Plan
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {apiKey ? (
              <div className="flex items-center gap-3 p-3 bg-cyber-bg rounded-xl border border-cyber-border animate-fade-in">
                <Key className="w-4 h-4 text-cyber-cyan flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-cyber-text">Active API Key</p>
                  <code className="text-xs text-cyber-muted font-mono truncate block">
                    {apiKey.slice(0, 16)}••••••••••••••••••••••••
                  </code>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={copyKey}
                    className="p-1.5 text-cyber-muted hover:text-cyber-cyan transition-colors rounded-lg hover:bg-cyber-cyan/10"
                    title="Copy key"
                  >
                    {copied ? <Check className="w-4 h-4 text-cyber-green" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={revokeKey}
                    className="p-1.5 text-cyber-muted hover:text-cyber-red transition-colors rounded-lg hover:bg-cyber-red/10"
                    title="Revoke key"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-cyber-bg rounded-xl border border-cyber-border/60 text-center space-y-3 animate-fade-in">
                <p className="text-xs text-cyber-muted">No API Key generated yet. Set up one for your automation needs.</p>
                <button
                  id="settings-generate-key-btn"
                  onClick={generateKey}
                  disabled={genLoading}
                  className="btn-outline-cyber inline-flex items-center gap-2 px-4 py-2 text-xs font-medium disabled:opacity-60"
                >
                  {genLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                  Generate API Key
                </button>
              </div>
            )}
          </div>
        )}
      </Section>

      {/* ── Subscription ───────────────────────────────────── */}
      <Section title="Subscription Plan">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {plans.map((plan) => {
            const Icon = plan.icon;
            return (
              <div
                key={plan.id}
                className={`p-4 rounded-xl border transition-all ${
                  (plan.id === userPlan || (plan.id === "free" && userPlan === "free_trial"))
                    ? "border-cyber-cyan/40 bg-cyber-cyan/5"
                    : "border-cyber-border hover:border-cyber-cyan/20"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    {Icon && <Icon className="w-4 h-4" style={{ color: plan.color }} />}
                    <span className="text-sm font-bold text-cyber-text">{plan.label}</span>
                  </div>
                  {(plan.id === userPlan || (plan.id === "free" && userPlan === "free_trial")) && (
                    <span className="badge badge-info text-[10px]">Current</span>
                  )}
                </div>
                <p className="text-xl font-extrabold mb-3" style={{ color: plan.color }}>
                  {plan.price}<span className="text-xs text-cyber-muted font-normal">/mo</span>
                </p>
                <ul className="space-y-1.5 mb-4">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-1.5 text-xs text-cyber-muted">
                      <Shield className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: plan.color }} />
                      {f}
                    </li>
                  ))}
                </ul>
                {!(plan.id === userPlan || (plan.id === "free" && userPlan === "free_trial")) && (
                  <button
                    onClick={() => {
                      setSelectedTier(plan.id);
                      setCheckoutModalOpen(true);
                      setPaymentMethod("stripe");
                      setMobileNo("");
                      setCheckoutError("");
                      setEasypaisaSuccess(false);
                    }}
                    className="w-full py-2 rounded-lg text-xs font-semibold transition-all border flex items-center justify-center gap-1"
                    style={{
                      borderColor: `${plan.color}40`,
                      color: plan.color,
                      background: `${plan.color}08`,
                    }}
                  >
                    Upgrade <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
        <div className="p-4 bg-cyber-bg rounded-xl border border-cyber-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-cyber-text flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-cyber-cyan" />
                Billing
              </p>
              <p className="text-xs text-cyber-muted mt-0.5">
                Manage your card, payments, and subscriptions via Stripe Portal.
              </p>
            </div>
            <button
              onClick={handleManageBilling}
              disabled={billingLoading}
              className="btn-outline-cyber px-4 py-2 text-xs font-medium flex items-center gap-2 disabled:opacity-60"
            >
              {billingLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Manage Billing
            </button>
          </div>
        </div>
      </Section>

      {/* ── Checkout Modal ────────────────────────────────── */}
      {checkoutModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="cyber-card max-w-md w-full p-6 border border-cyber-cyan/40 space-y-5 shadow-cyber relative">
            <button
              onClick={() => setCheckoutModalOpen(false)}
              className="absolute right-4 top-4 text-cyber-muted hover:text-cyber-cyan transition-colors"
            >
              ✕
            </button>
            <div className="w-12 h-12 bg-cyber-cyan/10 rounded-full border border-cyber-cyan/30 flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-cyber-cyan animate-pulse" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-cyber-text">Upgrade to {selectedTier?.toUpperCase()}</h3>
              <p className="text-xs text-cyber-muted mt-1">Select your preferred payment method below.</p>
            </div>

            {checkoutError && (
              <div className="p-3 bg-cyber-red/10 border border-cyber-red/30 rounded-lg text-xs text-cyber-red">
                {checkoutError}
              </div>
            )}

            {easypaisaSuccess ? (
              <div className="p-4 bg-cyber-green/10 border border-cyber-green/30 rounded-xl space-y-3">
                <CheckCircle2 className="w-8 h-8 text-cyber-green animate-bounce" />
                <h4 className="font-bold text-cyber-text text-sm">Payment Initiated!</h4>
                <p className="text-xs text-cyber-muted">
                  Please check your phone for a push prompt to enter your MPIN, or follow the SMS instructions. Your account will automatically upgrade once completed.
                </p>
                <button
                  onClick={() => {
                    setCheckoutModalOpen(false);
                    window.location.reload();
                  }}
                  className="btn-cyber w-full py-2 text-xs font-bold"
                >
                  Done
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Method selector */}
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "stripe", label: "Credit Card" },
                    { id: "jazzcash", label: "JazzCash" },
                    { id: "easypaisa", label: "EasyPaisa" },
                  ].map((method) => (
                    <button
                      key={method.id}
                      type="button"
                      onClick={() => {
                        setPaymentMethod(method.id);
                        setCheckoutError("");
                      }}
                      className={`py-3 px-2 border rounded-xl text-center text-xs transition-all ${
                        paymentMethod === method.id
                          ? "border-cyber-cyan bg-cyber-cyan/10 text-cyber-text"
                          : "border-cyber-border hover:border-cyber-cyan/30 text-cyber-muted"
                      }`}
                    >
                      {method.label}
                    </button>
                  ))}
                </div>

                {/* EasyPaisa Mobile Number Input */}
                {paymentMethod === "easypaisa" && (
                  <div className="space-y-2">
                    <label htmlFor="easypaisa-mobile" className="block text-xs font-medium text-cyber-text">
                      EasyPaisa Mobile Number
                    </label>
                    <input
                      id="easypaisa-mobile"
                      type="tel"
                      value={mobileNo}
                      onChange={(e) => setMobileNo(e.target.value)}
                      placeholder="03001234567"
                      className="scan-input w-full px-3 py-2.5 text-xs"
                    />
                    <p className="text-[10px] text-cyber-muted">
                      Enter the 11-digit mobile number associated with your EasyPaisa wallet.
                    </p>
                  </div>
                )}

                {/* Submit button */}
                <button
                  onClick={handleCheckoutSubmit}
                  disabled={checkoutLoading}
                  className="btn-cyber w-full py-3 text-sm font-bold flex items-center justify-center gap-1.5 disabled:opacity-60"
                >
                  {checkoutLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Processing...
                    </>
                  ) : (
                    <>
                      Pay Now <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
