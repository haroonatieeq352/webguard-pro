"use client";

import { useState } from "react";
import { Check, X, Zap, Shield, Building2, Rocket } from "lucide-react";

const plans = [
  {
    id: "free",
    name: "Free",
    icon: Zap,
    monthlyPrice: 0,
    yearlyPrice: 0,
    pkrMonthly: 0,
    badge: null,
    description: "Perfect to get started and see your website's health score.",
    color: "text-cyber-muted",
    borderColor: "border-cyber-border",
    btnClass: "btn-outline-cyber",
    btnText: "Start Free",
    features: [
      { text: "3 scans per month",                  included: true },
      { text: "Overall Health Score (0–100)",        included: true },
      { text: "SEO Audit (meta, H1, OG tags)",       included: true },
      { text: "Security Headers Check (8 headers)",  included: true },
      { text: "PageSpeed / Core Web Vitals",         included: true },
      { text: "AI Chatbot (5 messages/scan)",        included: true },
      { text: "Broken Links Scanner",                included: false },
      { text: "OWASP Top 10 DAST Scan",              included: false },
      { text: "SQLi / XSS Automated Tests",          included: false },
      { text: "PDF Reports",                         included: false },
      { text: "AI Auto-Remediation Code",            included: false },
    ],
  },
  {
    id: "pro",
    name: "Pro",
    icon: Shield,
    monthlyPrice: 9,
    yearlyPrice: 7,
    pkrMonthly: 2500,
    badge: "Most Popular",
    description: "For developers and freelancers who need real security scanning.",
    color: "text-cyber-cyan",
    borderColor: "border-cyber-cyan/50",
    btnClass: "btn-cyber",
    btnText: "Start Pro",
    features: [
      { text: "30 scans per month",                  included: true },
      { text: "Everything in Free",                  included: true },
      { text: "OWASP Top 10 DAST Scan (ZAP)",        included: true },
      { text: "SQLi / XSS / CSRF Auto Tests",        included: true },
      { text: "SSL / TLS Certificate Analysis",      included: true },
      { text: "Broken Links Scanner",                included: true },
      { text: "AI Security Analyst (unlimited)",     included: true },
      { text: "AI Auto-Remediation Code Fixes",      included: true },
      { text: "PDF Report (1/month)",                included: true },
      { text: "Web Cache Deception/Poisoning",       included: false },
      { text: "IDOR Detection",                      included: false },
    ],
  },
  {
    id: "business",
    name: "Business",
    icon: Building2,
    monthlyPrice: 19,
    yearlyPrice: 15,
    pkrMonthly: 5200,
    badge: "Best Value",
    description: "For software houses and agencies managing multiple client sites.",
    color: "text-purple-400",
    borderColor: "border-purple-500/40",
    btnClass: "btn-outline-cyber",
    btnText: "Start Business",
    features: [
      { text: "Unlimited scans",                      included: true },
      { text: "Everything in Pro",                    included: true },
      { text: "Web Cache Deception/Poisoning",        included: true },
      { text: "IDOR Detection",                       included: true },
      { text: "Subdomain Enumeration (Nmap)",         included: true },
      { text: "Custom Scan Scheduling",               included: true },
      { text: "AI Executive Summary Reports",         included: true },
      { text: "AI SEO Advisor (full)",                included: true },
      { text: "Unlimited PDF Reports",                included: true },
      { text: "API Key Access",                       included: true },
      { text: "White-Label PDF Reports",              included: false },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    icon: Rocket,
    monthlyPrice: 49,
    yearlyPrice: 39,
    pkrMonthly: 13500,
    badge: null,
    description: "For enterprises and agencies requiring full white-label capabilities.",
    color: "text-cyber-orange",
    borderColor: "border-cyber-orange/30",
    btnClass: "btn-outline-cyber",
    btnText: "Contact Sales",
    features: [
      { text: "Unlimited scans + team accounts",      included: true },
      { text: "Everything in Business",               included: true },
      { text: "White-Label PDF Reports",              included: true },
      { text: "Custom AI Persona (your brand)",       included: true },
      { text: "Team Roles & RBAC",                    included: true },
      { text: "Priority Support + SLA",               included: true },
      { text: "Dedicated Account Manager",            included: true },
      { text: "Custom Scan Policies",                 included: true },
      { text: "SSO / SAML Integration",               included: true },
      { text: "SOC 2 Compliance Reports",             included: true },
      { text: "API + Webhooks",                       included: true },
    ],
  },
];

export default function PricingSection() {
  const [isYearly, setIsYearly] = useState(false);
  const [showPKR,  setShowPKR]  = useState(false);

  return (
    <section id="pricing" className="section-padding relative">
      <div className="absolute inset-0 cyber-grid-bg opacity-20" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyber-cyan/30 bg-cyber-cyan/5 mb-5">
            <Shield className="w-3.5 h-3.5 text-cyber-cyan" />
            <span className="text-xs font-semibold text-cyber-cyan tracking-wide uppercase">
              Simple, Transparent Pricing
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black mb-5">
            <span className="gradient-text-white">Enterprise Security.</span>
            <br />
            <span className="gradient-text-cyan">Startup Pricing.</span>
          </h2>
          <p className="text-lg text-cyber-muted max-w-2xl mx-auto mb-8">
            Acunetix charges $375/month. We charge $9. Same OWASP testing.
            No compromise on quality.
          </p>

          {/* Toggles */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {/* Monthly/Yearly Toggle */}
            <div className="flex items-center gap-3 bg-cyber-card border border-cyber-border rounded-xl p-1">
              <button
                onClick={() => setIsYearly(false)}
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                  !isYearly
                    ? "bg-cyber-cyan text-cyber-bg"
                    : "text-cyber-muted hover:text-white"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setIsYearly(true)}
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${
                  isYearly
                    ? "bg-cyber-cyan text-cyber-bg"
                    : "text-cyber-muted hover:text-white"
                }`}
              >
                Yearly
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyber-green/20 text-cyber-green">
                  -20%
                </span>
              </button>
            </div>

            {/* USD/PKR Toggle */}
            <div className="flex items-center gap-3 bg-cyber-card border border-cyber-border rounded-xl p-1">
              <button
                onClick={() => setShowPKR(false)}
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                  !showPKR
                    ? "bg-cyber-cyan text-cyber-bg"
                    : "text-cyber-muted hover:text-white"
                }`}
              >
                USD $
              </button>
              <button
                onClick={() => setShowPKR(true)}
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                  showPKR
                    ? "bg-cyber-cyan text-cyber-bg"
                    : "text-cyber-muted hover:text-white"
                }`}
              >
                PKR ₨
              </button>
            </div>
          </div>
        </div>

        {/* ── Pricing Cards ─────────────────────────────────── */}
        {/*
          Alignment fix:
          - items-stretch  → all cards same height
          - Price block has minHeight so "Forever Free" / "Billed annually" lines
            don't push content down on other cards
          - Description fixed to 2-line height
          - Divider separates price area from feature list
          - features ul is flex-1 so cards fill remaining height evenly
        */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 items-stretch">
          {plans.map((plan) => {
            const Icon = plan.icon;
            const price = showPKR
              ? plan.pkrMonthly === 0
                ? 0
                : isYearly
                ? Math.round(plan.pkrMonthly * 0.8)
                : plan.pkrMonthly
              : isYearly
              ? plan.yearlyPrice
              : plan.monthlyPrice;
            const currency = showPKR ? "₨" : "$";
            const isPro = plan.id === "pro";

            return (
              <div
                key={plan.id}
                className={`relative cyber-card p-6 flex flex-col border ${plan.borderColor} transition-all duration-300 ${
                  isPro ? "shadow-cyber scale-[1.02]" : ""
                }`}
              >
                {/* Badge */}
                {plan.badge && (
                  <div
                    className={`absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold border whitespace-nowrap ${
                      plan.badge === "Most Popular"
                        ? "bg-cyber-cyan text-cyber-bg border-cyber-cyan"
                        : "bg-purple-500/20 text-purple-300 border-purple-500/40"
                    }`}
                  >
                    {plan.badge}
                  </div>
                )}

                {/* ── 1. Plan icon + name ─────────────────── */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                    <Icon className={`w-5 h-5 ${plan.color}`} />
                  </div>
                  <span className={`text-lg font-black ${plan.color}`}>{plan.name}</span>
                </div>

                {/* ── 2. Price block — FIXED HEIGHT so all cards align ── */}
                <div className="mb-1" style={{ minHeight: "64px" }}>
                  <div className="flex items-end gap-1">
                    <span className="text-4xl font-black text-white ticker">
                      {currency}{price}
                    </span>
                    {price > 0 && (
                      <span className="text-cyber-muted text-sm mb-1.5">/mo</span>
                    )}
                  </div>
                  {/* Sub-label row — always renders one fixed-height line */}
                  <div className="h-5 mt-0.5">
                    {price === 0 && (
                      <span className="text-cyber-green text-sm font-semibold">
                        Forever Free
                      </span>
                    )}
                    {isYearly && price > 0 && (
                      <p className="text-xs text-cyber-green">
                        Billed annually — save 20%
                      </p>
                    )}
                    {showPKR && price > 0 && !isYearly && (
                      <p className="text-xs text-cyber-muted">
                        via JazzCash / EasyPaisa / Card
                      </p>
                    )}
                  </div>
                </div>

                {/* ── 3. Description — FIXED 2-LINE HEIGHT ─── */}
                <p
                  className="text-xs text-cyber-muted leading-relaxed mb-5"
                  style={{ minHeight: "32px" }}
                >
                  {plan.description}
                </p>

                {/* ── 4. CTA Button — always at same position ─ */}
                <a
                  href={plan.id === "enterprise" ? "/contact" : "/auth/register"}
                  className={`${plan.btnClass} flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold rounded-xl text-center`}
                >
                  {plan.btnText}
                </a>

                {/* ── 5. Divider ──────────────────────────── */}
                <div className="border-t border-cyber-border/50 my-5" />

                {/* ── 6. Features list — flex-1 fills remaining height */}
                <ul className="space-y-2.5 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature.text} className="flex items-start gap-2.5">
                      {feature.included ? (
                        <Check className="w-4 h-4 text-cyber-green flex-shrink-0 mt-0.5" />
                      ) : (
                        <X className="w-4 h-4 text-cyber-muted/40 flex-shrink-0 mt-0.5" />
                      )}
                      <span
                        className={`text-xs leading-relaxed ${
                          feature.included ? "text-cyber-muted" : "text-cyber-muted/40"
                        }`}
                      >
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* Payment methods note */}
        <div className="mt-10 text-center">
          <p className="text-sm text-cyber-muted mb-3">
            Accepted payment methods
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {["💳 Visa / Mastercard", "🍎 Apple Pay", "🤖 Google Pay", "📱 JazzCash", "💚 EasyPaisa"].map((method) => (
              <span
                key={method}
                className="px-3 py-1.5 text-xs font-medium text-cyber-muted bg-cyber-card border border-cyber-border rounded-lg"
              >
                {method}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
