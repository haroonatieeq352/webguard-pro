import type { Metadata } from "next";
import DashboardShell from "@/components/dashboard/DashboardShell";

export const metadata: Metadata = {
  title: {
    default: "Dashboard — WebGuard Pro",
    template: "%s | WebGuard Pro Dashboard",
  },
  description: "Monitor your website security, SEO health, and scan results from your WebGuard Pro dashboard.",
  robots: { index: false, follow: false },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
