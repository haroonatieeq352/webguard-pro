import Link from "next/link";
import { Shield, Github, Linkedin, Twitter, Mail } from "lucide-react";

const footerLinks = {
  Product: [
    { label: "Features",      href: "#features" },
    { label: "Pricing",       href: "#pricing" },
    { label: "How It Works",  href: "#how-it-works" },
    { label: "Changelog",     href: "/changelog" },
    { label: "Roadmap",       href: "/roadmap" },
  ],
  Security: [
    { label: "OWASP Top 10",      href: "/docs/owasp" },
    { label: "SEO Audit",         href: "/docs/seo" },
    { label: "PDF Reports",       href: "/docs/reports" },
    { label: "AI Features",       href: "/docs/ai" },
    { label: "API Docs",          href: "/docs/api" },
  ],
  Company: [
    { label: "About Us",      href: "/about" },
    { label: "Blog",          href: "/blog" },
    { label: "Contact",       href: "/contact" },
    { label: "Careers",       href: "/careers" },
    { label: "Affiliate Program", href: "/affiliate" },
  ],
  Legal: [
    { label: "Privacy Policy",   href: "/privacy" },
    { label: "Terms of Service", href: "/terms" },
    { label: "Responsible Use",  href: "/responsible-use" },
    { label: "Security Policy",  href: "/security" },
    { label: "GDPR",             href: "/gdpr" },
  ],
};

const socialLinks = [
  { icon: Github,   href: "#", label: "GitHub"   },
  { icon: Twitter,  href: "#", label: "Twitter"  },
  { icon: Linkedin, href: "#", label: "LinkedIn" },
  { icon: Mail,     href: "mailto:hello@webguardpro.io", label: "Email" },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-cyber-border bg-cyber-dark">
      <div className="absolute inset-0 cyber-grid-bg opacity-20 pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Top CTA Banner */}
        <div className="py-12 border-b border-cyber-border flex flex-col lg:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-2xl sm:text-3xl font-black text-white mb-2">
              Ready to Secure Your Website?
            </h3>
            <p className="text-cyber-muted">
              Join thousands of developers. Free scan — no credit card required.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href="/auth/register"
              className="btn-cyber flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold rounded-xl"
            >
              <Shield className="w-4 h-4" />
              Start Free Scan
            </Link>
            <Link
              href="#pricing"
              className="btn-outline-cyber flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold rounded-xl"
            >
              View Pricing
            </Link>
          </div>
        </div>

        {/* Main Footer Grid */}
        <div className="py-12 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          {/* Logo + description */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2.5 mb-4 group w-fit">
              <div className="w-8 h-8 bg-gradient-to-br from-cyber-cyan to-[#0099BB] rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-cyber-bg" strokeWidth={2.5} />
              </div>
              <span className="text-base font-black text-white">
                WebGuard<span className="text-cyber-cyan">Pro</span>
              </span>
            </Link>
            <p className="text-xs text-cyber-muted leading-relaxed mb-5 max-w-[200px]">
              Enterprise-grade website security and SEO scanning at startup prices.
            </p>
            {/* Social Links */}
            <div className="flex gap-3">
              {socialLinks.map((s) => {
                const Icon = s.icon;
                return (
                  <a
                    key={s.label}
                    href={s.href}
                    aria-label={s.label}
                    className="w-8 h-8 rounded-lg bg-cyber-card border border-cyber-border flex items-center justify-center text-cyber-muted hover:text-cyber-cyan hover:border-cyber-cyan/40 transition-all"
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Footer Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">
                {category}
              </h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-xs text-cyber-muted hover:text-cyber-cyan transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="py-5 border-t border-cyber-border flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-cyber-muted">
            © {new Date().getFullYear()} WebGuard Pro. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-xs text-cyber-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyber-green animate-ping-slow" />
              All systems operational
            </span>
            <span>·</span>
            <span>Made with ❤️ in Pakistan</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
