import type { Metadata, Viewport } from "next";
import { Inter, Fira_Code } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
  display: "swap",
});

const firaCode = Fira_Code({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-fira-code",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://webguardpro.io"),
  title: {
    default: "WebGuard Pro — Website Security, SEO & Health Scanner",
    template: "%s | WebGuard Pro",
  },
  description:
    "Scan your website for OWASP Top 10 vulnerabilities, SEO issues, and performance problems. Get an instant health score with actionable AI-powered recommendations. Free scan available.",
  keywords: [
    "website security scanner",
    "OWASP vulnerability scanner",
    "SEO audit tool",
    "website health check",
    "penetration testing SaaS",
    "XSS scanner",
    "SQL injection detector",
    "Pakistan cybersecurity tool",
    "web application security",
    "free website scanner",
  ],
  authors: [{ name: "WebGuard Pro" }],
  creator: "WebGuard Pro",
  publisher: "WebGuard Pro",
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://webguardpro.io",
    siteName: "WebGuard Pro",
    title: "WebGuard Pro — Scan. Detect. Protect. Rank.",
    description:
      "Enterprise-grade website security and SEO scanning at startup pricing. OWASP Top 10 testing, AI-powered fixes, professional PDF reports.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "WebGuard Pro — Website Security Scanner",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "WebGuard Pro — Website Security & SEO Scanner",
    description:
      "OWASP Top 10 scanning, AI security advisor, SEO audit. Free scan available.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "https://webguardpro.io",
  },
};

export const viewport: Viewport = {
  themeColor: "#0A0E1A",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`scroll-smooth ${inter.variable} ${firaCode.variable}`}>
      <head>
        {/* Suppress chrome-extension/MetaMask noise during development */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const ignoredErrors = [
                  'chrome-extension://',
                  'MetaMask',
                  'Failed to connect to MetaMask',
                  'nkbihfbeogaeaoehlefnkodbefgpgknn'
                ];
                
                function isIgnored(errorMsg) {
                  if (!errorMsg) return false;
                  return ignoredErrors.some(term => errorMsg.includes(term));
                }

                function checkAndMute(event) {
                  const error = event.error || event.reason;
                  const message = event.message || (error && error.message) || '';
                  const stack = (error && error.stack) || '';
                  const filename = event.filename || '';

                  const isExtension = filename.includes('chrome-extension') || stack.includes('chrome-extension');

                  if (
                    isExtension ||
                    isIgnored(message) ||
                    isIgnored(stack)
                  ) {
                    event.stopImmediatePropagation();
                    if (event.preventDefault) event.preventDefault();
                    return true;
                  }
                  return false;
                }

                window.addEventListener('error', checkAndMute, true);
                window.addEventListener('unhandledrejection', checkAndMute, true);
              })();
            `
          }}
        />
        {/* JSON-LD Structured Data for SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "WebGuard Pro",
              applicationCategory: "SecurityApplication",
              operatingSystem: "Web",
              description:
                "All-in-one website security scanner with OWASP Top 10 testing, SEO audit, and AI-powered remediation.",
              url: "https://webguardpro.io",
              offers: {
                "@type": "Offer",
                price: "0",
                priceCurrency: "USD",
                description: "Free tier available — no credit card required",
              },
            }),
          }}
        />
      </head>
      <body className="bg-cyber-bg text-cyber-text antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
