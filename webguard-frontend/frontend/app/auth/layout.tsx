import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "Account — WebGuard Pro",
    template: "%s | WebGuard Pro",
  },
  description:
    "Sign in or create your WebGuard Pro account to start scanning websites for security vulnerabilities and SEO issues.",
  robots: {
    index: false, // Auth pages should not be indexed by search engines
    follow: false,
  },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
