"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Moon, Sun, Menu, Bell, Search } from "lucide-react";
import { useDashboard } from "./DashboardShell";

const pageTitles: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/new-scan": "New Scan",
  "/dashboard/results": "Scan Results",
  "/dashboard/history": "Scan History",
  "/dashboard/settings": "Settings",
};

export default function TopHeader() {
  const pathname = usePathname();
  const { theme, toggleTheme, setSidebarOpen } = useDashboard();
  const [initials, setInitials] = useState("");

  useEffect(() => {
    const rawUser = localStorage.getItem("wg-user");
    if (rawUser) {
      try {
        const u = JSON.parse(rawUser);
        const name = u.full_name || u.email.split("@")[0];
        const userInitials = name
          .split(" ")
          .map((n: string) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2) || "U";
        setInitials(userInitials);
      } catch (e) {
        console.error("Failed to parse user initials", e);
      }
    }
  }, []);

  const title = Object.entries(pageTitles).find(([key]) =>
    pathname === key || (key !== "/dashboard" && pathname.startsWith(key))
  )?.[1] ?? "Dashboard";

  return (
    <header className="dashboard-header h-16 flex items-center px-4 md:px-6 gap-4 border-b border-cyber-border bg-cyber-card/80 backdrop-blur-sm flex-shrink-0 sticky top-0 z-10">
      {/* Mobile hamburger */}
      <button
        id="dashboard-menu-btn"
        className="lg:hidden text-cyber-muted hover:text-cyber-cyan transition-colors"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      <div className="flex items-center gap-2">
        <h1 className="text-base font-semibold text-cyber-text">{title}</h1>
      </div>

      {/* Search bar (desktop) */}
      <div className="hidden md:flex items-center gap-2 flex-1 max-w-sm ml-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-muted" />
          <input
            type="search"
            placeholder="Search scans, URLs..."
            className="scan-input w-full pl-9 pr-4 py-2 text-sm"
          />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-2">
        {/* Notification bell */}
        <button
          className="relative p-2 text-cyber-muted hover:text-cyber-cyan transition-colors rounded-lg hover:bg-cyber-cyan/10"
          aria-label="Notifications"
          id="dashboard-notifications-btn"
        >
          <Bell className="w-5 h-5" />
          {/* Badge */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyber-red rounded-full ring-2 ring-cyber-card" />
        </button>

        {/* Theme toggle */}
        <button
          id="dashboard-theme-toggle"
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-cyber-border hover:border-cyber-cyan/40 transition-all text-sm font-medium text-cyber-muted hover:text-cyber-text"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? (
            <>
              <Sun className="w-4 h-4" />
              <span className="hidden sm:inline text-xs">Light</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4" />
              <span className="hidden sm:inline text-xs">Dark</span>
            </>
          )}
        </button>

        {/* User avatar */}
        <button
          id="dashboard-user-avatar"
          className="w-8 h-8 rounded-full bg-gradient-to-br from-cyber-cyan to-purple-500 flex items-center justify-center text-cyber-bg text-xs font-bold hover:ring-2 hover:ring-cyber-cyan/40 transition-all"
          aria-label="User menu"
        >
          {initials || "U"}
        </button>
      </div>
    </header>
  );
}
