"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Shield, Menu, X, ChevronDown, Zap } from "lucide-react";

const navLinks = [
  { label: "Features",   href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Pricing",    href: "#pricing" },
  {
    label: "Solutions",
    href: "#",
    children: [
      { label: "For Developers",    href: "#", icon: "💻" },
      { label: "For Agencies",      href: "#", icon: "🏢" },
      { label: "For Software Houses", href: "#", icon: "🛡️" },
      { label: "For SMBs",          href: "#", icon: "📈" },
    ],
  },
];

export default function Navbar() {
  const [isOpen,       setIsOpen]       = useState(false);
  const [scrolled,     setScrolled]     = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-cyber-bg/95 backdrop-blur-md border-b border-cyber-border shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
          : "bg-transparent"
      }`}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-18">

          {/* ── Logo ─────────────────────────────────────── */}
          <Link href="/" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="relative w-9 h-9">
              <div className="absolute inset-0 bg-cyber-cyan/20 rounded-lg blur-md group-hover:bg-cyber-cyan/30 transition-all" />
              <div className="relative w-9 h-9 bg-gradient-to-br from-cyber-cyan to-[#0099BB] rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-cyber-bg" strokeWidth={2.5} />
              </div>
            </div>
            <div className="flex flex-col -space-y-0.5">
              <span className="text-lg font-black text-white tracking-tight leading-none">
                WebGuard
                <span className="text-cyber-cyan ml-1">Pro</span>
              </span>
              <span className="text-[9px] text-cyber-muted font-medium tracking-widest uppercase">
                Security · SEO · AI
              </span>
            </div>
          </Link>

          {/* ── Desktop Nav ───────────────────────────────── */}
          <div className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) =>
              link.children ? (
                <div
                  key={link.label}
                  className="relative"
                  onMouseEnter={() => setActiveDropdown(link.label)}
                  onMouseLeave={() => setActiveDropdown(null)}
                >
                  <button className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-cyber-muted hover:text-white transition-colors rounded-lg hover:bg-white/5">
                    {link.label}
                    <ChevronDown
                      className={`w-3.5 h-3.5 transition-transform duration-200 ${
                        activeDropdown === link.label ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  {activeDropdown === link.label && (
                    <div className="absolute top-full left-0 mt-1 w-56 bg-cyber-card border border-cyber-border rounded-xl shadow-cyber overflow-hidden">
                      <div className="p-1.5">
                        {link.children.map((child) => (
                          <Link
                            key={child.label}
                            href={child.href}
                            className="flex items-center gap-3 px-3 py-2.5 text-sm text-cyber-muted hover:text-white hover:bg-white/5 rounded-lg transition-all group"
                          >
                            <span className="text-base">{child.icon}</span>
                            <span className="group-hover:text-cyber-cyan transition-colors">
                              {child.label}
                            </span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  key={link.label}
                  href={link.href}
                  className="px-4 py-2 text-sm font-medium text-cyber-muted hover:text-white transition-colors rounded-lg hover:bg-white/5"
                >
                  {link.label}
                </Link>
              )
            )}
          </div>

          {/* ── Desktop CTA ───────────────────────────────── */}
          <div className="hidden lg:flex items-center gap-3">
            <Link
              href="/auth/login"
              className="px-4 py-2 text-sm font-semibold text-cyber-muted hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/auth/register"
              className="btn-cyber flex items-center gap-2 px-5 py-2.5 text-sm font-bold rounded-lg"
            >
              <Zap className="w-4 h-4" />
              Free Scan
            </Link>
          </div>

          {/* ── Mobile Menu Toggle ─────────────────────────── */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 rounded-lg text-cyber-muted hover:text-white hover:bg-white/5 transition-all"
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* ── Mobile Menu ───────────────────────────────────── */}
        {isOpen && (
          <div className="lg:hidden border-t border-cyber-border bg-cyber-bg/98 backdrop-blur-md">
            <div className="px-2 py-4 space-y-1">
              {navLinks.map((link) => (
                <div key={link.label}>
                  <Link
                    href={link.href}
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 text-sm font-medium text-cyber-muted hover:text-white hover:bg-white/5 rounded-lg transition-all"
                  >
                    {link.label}
                  </Link>
                  {link.children && (
                    <div className="ml-4 mt-1 space-y-1">
                      {link.children.map((child) => (
                        <Link
                          key={child.label}
                          href={child.href}
                          onClick={() => setIsOpen(false)}
                          className="flex items-center gap-2 px-4 py-2 text-xs text-cyber-muted hover:text-cyber-cyan transition-colors rounded-lg"
                        >
                          <span>{child.icon}</span>
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {/* Mobile CTA */}
              <div className="pt-3 flex flex-col gap-2">
                <Link
                  href="/auth/login"
                  onClick={() => setIsOpen(false)}
                  className="block text-center px-4 py-3 text-sm font-semibold text-cyber-muted border border-cyber-border rounded-lg hover:border-cyber-cyan/40 transition-all"
                >
                  Sign In
                </Link>
                <Link
                  href="/auth/register"
                  onClick={() => setIsOpen(false)}
                  className="btn-cyber flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold rounded-lg"
                >
                  <Zap className="w-4 h-4" />
                  Start Free Scan
                </Link>
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
