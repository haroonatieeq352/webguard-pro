"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ScanSearch,
  History,
  FileBarChart2,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
  LogOut,
  X,
  Crown,
  Zap,
} from "lucide-react";
import { useDashboard } from "./DashboardShell";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  exact?: boolean;
}

const navItems: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/new-scan", label: "New Scan", icon: ScanSearch },
  { href: "/dashboard/history", label: "Scan History", icon: History },
  { href: "/dashboard/results", label: "Latest Results", icon: FileBarChart2 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

const planConfig = {
  free_trial: { label: "Free Trial", color: "#00D4FF", icon: Zap },
  free:       { label: "Free",       color: "#94A3B8", icon: null },
  pro:        { label: "Pro",        color: "#00D4FF", icon: Zap },
  business:   { label: "Business",   color: "#A78BFA", icon: Crown },
  enterprise: { label: "Enterprise", color: "#FFD60A", icon: Crown },
};

export default function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen, sidebarCollapsed, setSidebarCollapsed } = useDashboard();
  const [currentUser, setCurrentUser] = useState({
    name: "",
    email: "",
    plan: "free" as keyof typeof planConfig,
    initials: "",
  });

  useEffect(() => {
    const rawUser = localStorage.getItem("wg-user");
    if (rawUser) {
      try {
        const u = JSON.parse(rawUser);
        const name = u.full_name || u.email.split("@")[0];
        const initials = name
          .split(" ")
          .map((n: string) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2) || "HA";
        
        setCurrentUser({
          name: name,
          email: u.email,
          plan: (u.subscription_tier as keyof typeof planConfig) || "free",
          initials: initials,
        });
      } catch (e) {
        console.error("Failed to parse user", e);
      }
    }
  }, []);

  const plan = planConfig[currentUser.plan];
  const PlanIcon = plan.icon;

  const isActive = (item: (typeof navItems)[0]) => {
    if (item.exact) return pathname === item.href;
    return pathname.startsWith(item.href);
  };

  function handleLogout() {
    localStorage.removeItem("wg-token");
    localStorage.removeItem("wg-refresh-token");
    localStorage.removeItem("wg-user");
    window.location.href = "/";
  }

  return (
    <>
      {/* ── Desktop Sidebar ─────────────────────────────────── */}
      <aside
        className={`
          hidden lg:flex flex-col h-full
          dashboard-sidebar border-r border-cyber-border
          transition-all duration-300 ease-in-out
          ${sidebarCollapsed ? "w-[68px]" : "w-64"}
          bg-gradient-to-b from-cyber-card to-cyber-bg flex-shrink-0
        `}
      >
        <SidebarContent
          collapsed={sidebarCollapsed}
          onCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          navItems={navItems}
          isActive={isActive}
          plan={plan}
          PlanIcon={PlanIcon}
          user={currentUser}
          onLogout={handleLogout}
          onClose={null}
        />
      </aside>

      {/* ── Mobile Sidebar ──────────────────────────────────── */}
      <aside
        className={`
          fixed lg:hidden top-0 left-0 h-full z-30 w-72 flex flex-col
          dashboard-sidebar border-r border-cyber-border
          bg-gradient-to-b from-cyber-card to-cyber-bg
          transition-transform duration-300 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <SidebarContent
          collapsed={false}
          onCollapse={null}
          navItems={navItems}
          isActive={isActive}
          plan={plan}
          PlanIcon={PlanIcon}
          user={currentUser}
          onLogout={handleLogout}
          onClose={() => setSidebarOpen(false)}
        />
      </aside>
    </>
  );
}

/* ── Sidebar Content ─────────────────────────────────────── */
function SidebarContent({
  collapsed,
  onCollapse,
  navItems,
  isActive,
  plan,
  PlanIcon,
  user,
  onLogout,
  onClose,
}: {
  collapsed: boolean;
  onCollapse: (() => void) | null;
  navItems: NavItem[];
  isActive: (item: NavItem) => boolean;
  plan: (typeof planConfig)[keyof typeof planConfig];
  PlanIcon: React.ElementType | null;
  user: { name: string; email: string; plan: string; initials: string; };
  onLogout: () => void;
  onClose: (() => void) | null;
}) {
  return (
    <>
      {/* Logo header */}
      <div
        className={`flex items-center h-16 px-4 border-b border-cyber-border flex-shrink-0 ${
          collapsed ? "justify-center" : "justify-between"
        }`}
      >
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2 group">
            <div className="relative">
              <Shield className="w-7 h-7 text-cyber-cyan group-hover:scale-110 transition-transform" />
              <div className="absolute inset-0 bg-cyber-cyan/20 rounded-full blur-sm" />
            </div>
            <span className="text-sm font-bold gradient-text-cyan">WebGuard Pro</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/">
            <Shield className="w-7 h-7 text-cyber-cyan hover:scale-110 transition-transform" />
          </Link>
        )}

        {/* Mobile close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="text-cyber-muted hover:text-cyber-text transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Desktop collapse toggle */}
        {onCollapse && (
          <button
            onClick={onCollapse}
            className="text-cyber-muted hover:text-cyber-cyan transition-colors p-1 rounded-lg hover:bg-cyber-cyan/10"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 overflow-y-auto dashboard-scroll">
        <div className="space-y-0.5 px-2">
          {navItems.map((item) => {
            const active = isActive(item);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-200 group
                  ${active
                    ? "nav-active bg-cyber-cyan/10 text-cyber-cyan"
                    : "text-cyber-muted hover:text-cyber-text hover:bg-cyber-cyan/5"
                  }
                  ${collapsed ? "justify-center" : ""}
                `}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 ${
                    active ? "text-cyber-cyan" : "text-cyber-muted group-hover:text-cyber-text"
                  } transition-colors`}
                />
                {!collapsed && <span>{item.label}</span>}
                {!collapsed && active && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyber-cyan" />
                )}
              </Link>
            );
          })}
        </div>

        {/* New scan quick button */}
        {!collapsed && (
          <div className="px-4 mt-4">
            <Link
              href="/dashboard/new-scan"
              id="sidebar-new-scan-btn"
              className="btn-cyber w-full flex items-center justify-center gap-2 py-2.5 text-xs font-bold"
            >
              <ScanSearch className="w-4 h-4" />
              Start New Scan
            </Link>
          </div>
        )}
      </nav>

      {/* User profile at bottom */}
      <div className={`border-t border-cyber-border p-3 flex-shrink-0 ${collapsed ? "px-2" : ""}`}>
        {/* Plan badge */}
        {!collapsed && (
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-lg mb-2 border"
            style={{
              background: `${plan.color}10`,
              borderColor: `${plan.color}30`,
            }}
          >
            {PlanIcon && (
              <PlanIcon className="w-3.5 h-3.5" style={{ color: plan.color }} />
            )}
            <span className="text-xs font-semibold" style={{ color: plan.color }}>
              {plan.label} Plan
            </span>
            <Link
              href="/dashboard/settings"
              className="ml-auto text-xs text-cyber-muted hover:text-cyber-cyan transition-colors"
            >
              Upgrade
            </Link>
          </div>
        )}

        {/* User info */}
        <div className={`flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyber-cyan to-purple-500 flex items-center justify-center text-cyber-bg text-xs font-bold flex-shrink-0">
            {user.initials}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-cyber-text truncate">{user.name}</p>
              <p className="text-xs text-cyber-muted truncate">{user.email}</p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={onLogout}
              className="text-cyber-muted hover:text-cyber-red transition-colors"
              title="Logout"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </>
  );
}
