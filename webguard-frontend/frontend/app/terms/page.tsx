"use client";

import Link from "next/link";
import { Shield, ArrowLeft, Terminal } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid-bg text-cyber-text font-sans relative overflow-x-hidden">
      {/* Glow Orbs */}
      <div className="absolute top-10 left-10 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-cyber-purple/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl mx-auto px-4 py-12 relative z-10 animate-fade-in-up">
        {/* Header Navigation */}
        <div className="flex justify-between items-center mb-10 border-b border-cyber-border pb-6">
          <Link href="/auth/register" className="flex items-center gap-2 text-sm text-cyber-muted hover:text-cyber-cyan transition-colors group">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Register
          </Link>
          <Link href="/" className="flex items-center gap-2 group">
            <Shield className="w-6 h-6 text-cyber-cyan group-hover:rotate-12 transition-transform" />
            <span className="font-bold text-sm text-white tracking-wide">WebGuard <span className="text-cyber-cyan">Pro</span></span>
          </Link>
        </div>

        {/* Content Box */}
        <div className="cyber-card p-8 sm:p-10 shadow-cyber">
          <div className="flex items-center gap-3 mb-6">
            <Terminal className="w-6 h-6 text-cyber-cyan" />
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Terms of Service</h1>
          </div>

          <p className="text-sm text-cyber-muted mb-6">
            Last Updated: June 1, 2026. Please read these terms carefully before using WebGuard Pro.
          </p>

          <div className="space-y-6 text-sm leading-relaxed text-cyber-text">
            {/* Section 1 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">01.</span> Acceptance of Terms
              </h2>
              <p className="text-cyber-muted">
                By accessing, scanning, or registering an account on WebGuard Pro, you agree to comply with and be bound by these Terms of Service. If you do not agree, you are prohibited from using the platform.
              </p>
            </section>

            {/* Section 2 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">02.</span> Scope of Service & Scan Limits
              </h2>
              <p className="text-cyber-muted">
                WebGuard Pro provides website security auditing, SEO audits, and code analysis services. Access depends on your tier:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-cyber-muted">
                <li><span className="text-white font-semibold">Free Trial:</span> Valid for 14 days, limited to a total of 2 basic scans. No credit card required.</li>
                <li><span className="text-white font-semibold">Free Tier:</span> Activated after trial expiry. Limited to 3 basic scans per calendar month.</li>
                <li><span className="text-white font-semibold">Pro Tier ($9/mo):</span> Includes up to 30 scans per month, OWASP DAST, SSL audits, and PDF report downloads.</li>
                <li><span className="text-white font-semibold">Business/Enterprise Tier:</span> Includes unlimited scans, advanced cache attacks audits, subdomain DNS enumerations, and white-labeling features.</li>
              </ul>
            </section>

            {/* Section 3 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">03.</span> Scanning Authorization & Restrictions
              </h2>
              <div className="bg-cyber-red/10 border border-cyber-red/20 rounded-lg p-4 mb-3 text-cyber-muted">
                <span className="text-cyber-red font-bold uppercase tracking-wider block mb-1">CRITICAL REQUIREMENT</span>
                You represent and warrant that you are the owner, administrator, or have express permission to run security checks on the target URL submitted. Running DAST active scanners or port probes against unauthorized systems is illegal.
              </div>
              <p className="text-cyber-muted">
                Our scan engines check for security configurations and block private networks (RFC 1918) automatically. You may not bypass these controls. Exposing or hacking systems using reports is prohibited.
              </p>
            </section>

            {/* Section 4 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">04.</span> Subscription Payments & Webhooks
              </h2>
              <p className="text-cyber-muted">
                Subscribing to Pro, Business, or Enterprise tiers commits you to recurring billing. Payment integrations are powered securely via Stripe, JazzCash, or EasyPaisa. Subscriptions upgrade instantly upon verification of the payment gateway callback webhook.
              </p>
            </section>

            {/* Section 5 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">05.</span> Limitation of Liability
              </h2>
              <p className="text-cyber-muted">
                WebGuard Pro is an automated assessment tool. It does not replace physical penetration testing or comprehensive audits. We assume no liability for any security breaches, outages, loss of data, or damages originating from vulnerabilities that were flagged or missed by our scan engine.
              </p>
            </section>
          </div>

          {/* Accept CTA in terms */}
          <div className="mt-10 pt-6 border-t border-cyber-border/40 text-center">
            <Link href="/auth/register" className="btn-cyber px-6 py-2.5 text-xs font-bold inline-block">
              Return and Accept Terms
            </Link>
          </div>
        </div>

        {/* Footer Note */}
        <p className="text-center text-xs text-cyber-muted mt-8">
          © 2026 WebGuard Pro. All rights reserved. Under governance of Pakistani cybersecurity frameworks and international SaaS principles.
        </p>
      </div>
    </div>
  );
}
