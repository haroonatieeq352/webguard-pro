"use client";

import Link from "next/link";
import { Shield, ArrowLeft, Eye } from "lucide-react";

export default function PrivacyPage() {
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
            <Eye className="w-6 h-6 text-cyber-cyan" />
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Privacy Policy</h1>
          </div>

          <p className="text-sm text-cyber-muted mb-6">
            Last Updated: June 1, 2026. This policy explains how we gather, store, and protect your information.
          </p>

          <div className="space-y-6 text-sm leading-relaxed text-cyber-text">
            {/* Section 1 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">01.</span> Information We Collect
              </h2>
              <p className="text-cyber-muted">
                To perform security audits, we collect and store:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-cyber-muted">
                <li><span className="text-white font-semibold">Account Information:</span> Your name, email address, password hashes (argon2id secured), and preferences.</li>
                <li><span className="text-white font-semibold">Scan Information:</span> Target URLs, scanned dates, compiled scores, vulnerabilities, and payload outputs.</li>
                <li><span className="text-white font-semibold">Billing Information:</span> Transacted invoices and subscription tiers. Credit card details are handled exclusively by Stripe, and local wallets are handled by JazzCash/EasyPaisa. We do not store card PINs.</li>
              </ul>
            </section>

            {/* Section 2 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">02.</span> Scan Result Privacy
              </h2>
              <p className="text-cyber-muted">
                All security scans, vulnerabilities detected, and generated PDF reports are linked securely to your account ID. They are private and cannot be read by other users. 
              </p>
              <div className="bg-cyber-cyan/5 border border-cyber-cyan/20 rounded-lg p-4 mb-3 text-cyber-muted">
                <span className="text-cyber-cyan font-bold uppercase tracking-wider block mb-1">HMAC REPORT AUTHENTICITY</span>
                If you download a PDF report, a public cryptographic HMAC-SHA256 signature is included. The report is only visible to unauthenticated public visitors if you share your unique verification link or report hash.
              </div>
            </section>

            {/* Section 3 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">03.</span> Cookies & Local Storage
              </h2>
              <p className="text-cyber-muted">
                We use local browser storage and standard cookies to manage JWT access and refresh tokens, user themes (Dark/Light Cyber Shield toggles), and active UI states. Rejecting these items will break dashboard authorization functions.
              </p>
            </section>

            {/* Section 4 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">04.</span> Data Security & Retention
              </h2>
              <p className="text-cyber-muted">
                We implement industry-standard encryption controls for data in transit and at rest. Account profiles remain active until deleted. Active scans and logs are archived securely. You can request complete profile removal and API key revocation through settings.
              </p>
            </section>

            {/* Section 5 */}
            <section className="space-y-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyber-cyan font-mono text-sm">05.</span> Contact Us
              </h2>
              <p className="text-cyber-muted">
                For questions regarding data processing, security compliance, or to report scan engine abuses, contact our privacy department at <a href="mailto:privacy@webguardpro.io" className="text-cyber-cyan hover:underline">privacy@webguardpro.io</a> or the owner at <a href="mailto:haroonatieeq6@gmail.com" className="text-cyber-cyan hover:underline">haroonatieeq6@gmail.com</a>.
              </p>
            </section>
          </div>

          {/* Accept CTA in privacy */}
          <div className="mt-10 pt-6 border-t border-cyber-border/40 text-center">
            <Link href="/auth/register" className="btn-cyber px-6 py-2.5 text-xs font-bold inline-block">
              Return and Accept Privacy Policy
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
