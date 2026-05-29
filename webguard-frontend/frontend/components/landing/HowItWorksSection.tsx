"use client";

import { Globe, Search, FileText, Bot } from "lucide-react";

const steps = [
  {
    step: "01",
    icon: Globe,
    color: "text-cyber-cyan",
    bg: "bg-cyber-cyan/10",
    border: "border-cyber-cyan/20",
    title: "Enter Your URL",
    description:
      "Paste your website URL into the scanner. No setup, no installation, no credit card required.",
  },
  {
    step: "02",
    icon: Search,
    color: "text-cyber-orange",
    bg: "bg-cyber-orange/10",
    border: "border-cyber-orange/20",
    title: "We Scan Everything",
    description:
      "Our engine checks OWASP vulnerabilities, SEO issues, performance metrics, security headers and code quality simultaneously.",
  },
  {
    step: "03",
    icon: Bot,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    title: "AI Analyzes Results",
    description:
      "Claude AI reads your scan data and generates plain-English explanations plus exact code fixes for your tech stack.",
  },
  {
    step: "04",
    icon: FileText,
    color: "text-cyber-green",
    bg: "bg-cyber-green/10",
    border: "border-cyber-green/20",
    title: "Download Report",
    description:
      "Get a professional PDF report — executive summary for your boss, technical details for your developer.",
  },
];

const testimonials = [
  {
    name: "Ahmed Raza",
    role: "Full Stack Developer, Lahore",
    avatar: "AR",
    color: "bg-cyber-cyan",
    quote:
      "Found 3 XSS vulnerabilities on my client's site in 60 seconds. Fixed them same day. Client was impressed. Worth every rupee.",
    rating: 5,
  },
  {
    name: "Fatima Khan",
    role: "Digital Agency Owner, Karachi",
    avatar: "FK",
    color: "bg-purple-500",
    quote:
      "We run WebGuard Pro on every client site before delivery. The white-label PDF reports make us look professional. Best $19/month investment.",
    rating: 5,
  },
  {
    name: "Usman Ali",
    role: "IT Manager, Software House Islamabad",
    avatar: "UA",
    color: "bg-cyber-green",
    quote:
      "The AI chatbot is genuinely useful. I asked it to explain SSRF in Urdu and it gave a perfect explanation with Django-specific fixes.",
    rating: 5,
  },
];

export default function HowItWorksSection() {
  return (
    <>
      {/* ── How It Works ────────────────────────────────────── */}
      <section id="how-it-works" className="section-padding relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyber-cyan/3 to-transparent pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyber-cyan/30 bg-cyber-cyan/5 mb-5">
              <Search className="w-3.5 h-3.5 text-cyber-cyan" />
              <span className="text-xs font-semibold text-cyber-cyan tracking-wide uppercase">
                How It Works
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black mb-4">
              <span className="gradient-text-white">From URL to Report</span>
              <br />
              <span className="gradient-text-cyan">in Under 60 Seconds</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={step.step} className="relative">
                  {/* Connector line */}
                  {idx < steps.length - 1 && (
                    <div className="hidden lg:block absolute top-10 left-full w-full h-px bg-gradient-to-r from-cyber-border to-transparent z-0 -translate-y-1/2" />
                  )}
                  <div className={`relative z-10 cyber-card p-6 h-full border ${step.border}`}>
                    {/* Step number */}
                    <div className="text-5xl font-black text-white/5 absolute top-4 right-4 font-mono select-none">
                      {step.step}
                    </div>
                    {/* Icon */}
                    <div className={`w-12 h-12 rounded-xl ${step.bg} border ${step.border} flex items-center justify-center mb-4`}>
                      <Icon className={`w-6 h-6 ${step.color}`} />
                    </div>
                    <h3 className="text-base font-bold text-white mb-2">{step.title}</h3>
                    <p className="text-sm text-cyber-muted leading-relaxed">{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Testimonials ─────────────────────────────────────── */}
      <section className="section-padding relative overflow-hidden">
        <div className="absolute inset-0 cyber-grid-bg opacity-20" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-purple-500/5 blur-[100px] pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-black mb-3">
              <span className="gradient-text-white">Trusted by Developers</span>
              <br />
              <span className="gradient-text-cyan">Across Pakistan &amp; Beyond</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <div key={t.name} className="cyber-card p-6">
                {/* Stars */}
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: t.rating }).map((_, i) => (
                    <span key={i} className="text-cyber-orange text-sm">★</span>
                  ))}
                </div>
                {/* Quote */}
                <p className="text-sm text-cyber-muted leading-relaxed mb-5 italic">
                  &ldquo;{t.quote}&rdquo;
                </p>
                {/* Author */}
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-full ${t.color} flex items-center justify-center text-xs font-bold text-white`}>
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{t.name}</p>
                    <p className="text-xs text-cyber-muted">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
