"use client";

import { Shield, TrendingUp, Zap, FileText, Bot, Eye } from "lucide-react";

const features = [
  {
    icon: Shield,
    color: "text-cyber-red",
    bg: "bg-cyber-red/10",
    border: "border-cyber-red/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(255,71,87,0.15)]",
    title: "OWASP Top 10 Scanner",
    description:
      "Automated DAST scanning for all OWASP 2025 vulnerabilities — SQLi, XSS, CSRF, SSRF, Web Cache Poisoning, IDOR and more. Real evidence with PoC.",
    tags: ["SQLi", "XSS", "CSRF", "SSRF", "IDOR"],
  },
  {
    icon: TrendingUp,
    color: "text-cyber-cyan",
    bg: "bg-cyber-cyan/10",
    border: "border-cyber-cyan/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(0,212,255,0.15)]",
    title: "Deep SEO Audit",
    description:
      "Full SEO health check: meta tags, H1/H2 structure, Open Graph, sitemap, canonical tags, keyword density, Core Web Vitals and mobile-friendliness.",
    tags: ["Meta Tags", "Core Web Vitals", "Sitemap", "OG Tags"],
  },
  {
    icon: Zap,
    color: "text-cyber-orange",
    bg: "bg-cyber-orange/10",
    border: "border-cyber-orange/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(255,107,53,0.15)]",
    title: "Performance Analysis",
    description:
      "PageSpeed Insights integration — LCP, FID, CLS metrics. Un-minified JS detection, mixed content, broken links and render-blocking resources.",
    tags: ["LCP", "CLS", "FID", "PageSpeed"],
  },
  {
    icon: Bot,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(167,139,250,0.15)]",
    title: "AI Security Analyst",
    description:
      "Ask anything about your scan results. AI explains vulnerabilities in plain English, generates stack-specific code fixes and prioritizes remediation steps.",
    tags: ["Claude AI", "Code Fixes", "Urdu/English", "Context-Aware"],
  },
  {
    icon: FileText,
    color: "text-cyber-green",
    bg: "bg-cyber-green/10",
    border: "border-cyber-green/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(46,213,115,0.15)]",
    title: "Professional PDF Reports",
    description:
      "One-click executive + technical PDF reports. Designed for both non-technical business owners and developers. White-label option for agencies.",
    tags: ["Executive Summary", "Technical Details", "White-Label", "S3 Stored"],
  },
  {
    icon: Eye,
    color: "text-cyber-cyan",
    bg: "bg-cyber-cyan/10",
    border: "border-cyber-cyan/20",
    glow: "group-hover:shadow-[0_0_30px_rgba(0,212,255,0.15)]",
    title: "Security Headers Check",
    description:
      "Full HTTP security headers analysis — CSP, HSTS, X-Frame-Options, Referrer-Policy and more. Instant scoring with exact recommended values.",
    tags: ["CSP", "HSTS", "X-Frame-Options", "8 Headers"],
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="section-padding relative">
      {/* Background */}
      <div className="absolute inset-0 cyber-grid-bg opacity-30" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyber-cyan/30 bg-cyber-cyan/5 mb-5">
            <Zap className="w-3.5 h-3.5 text-cyber-cyan" />
            <span className="text-xs font-semibold text-cyber-cyan tracking-wide uppercase">
              Everything in One Platform
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black mb-5">
            <span className="gradient-text-white">All-in-One</span>{" "}
            <span className="gradient-text-cyan">Website Intelligence</span>
          </h2>
          <p className="text-lg text-cyber-muted max-w-2xl mx-auto">
            Security scanning, SEO auditing, performance analysis and AI-powered
            remediation — replace 4 separate tools with one affordable platform.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className={`group cyber-card p-6 cursor-default transition-all duration-300 ${feature.glow}`}
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl ${feature.bg} border ${feature.border} flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110`}>
                  <Icon className={`w-6 h-6 ${feature.color}`} strokeWidth={1.5} />
                </div>

                {/* Title */}
                <h3 className="text-lg font-bold text-white mb-3 group-hover:text-cyber-cyan transition-colors">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-cyber-muted leading-relaxed mb-5">
                  {feature.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2">
                  {feature.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 text-[10px] font-semibold rounded-md bg-white/5 text-cyber-muted border border-white/5 tracking-wide uppercase"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA strip */}
        <div className="mt-14 p-6 rounded-2xl border border-cyber-cyan/20 bg-cyber-cyan/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-white font-bold text-lg">
              All features. One dashboard.
            </p>
            <p className="text-cyber-muted text-sm mt-1">
              Replace Acunetix ($375/mo) + SEMrush ($129/mo) with WebGuard Pro from just $9/month.
            </p>
          </div>
          <a
            href="#pricing"
            className="btn-cyber flex items-center gap-2 px-6 py-3 text-sm font-bold rounded-xl whitespace-nowrap"
          >
            See All Plans <span className="text-base">→</span>
          </a>
        </div>
      </div>
    </section>
  );
}
