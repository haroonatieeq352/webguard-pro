"use client";

import { useState, createContext, useContext, useEffect } from "react";
import Sidebar from "./Sidebar";
import TopHeader from "./TopHeader";

/* ── Context ─────────────────────────────────────────────── */
interface DashboardCtx {
  theme: "dark" | "light";
  toggleTheme: () => void;
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
}

export const DashboardContext = createContext<DashboardCtx>({
  theme: "dark",
  toggleTheme: () => {},
  sidebarOpen: false,
  setSidebarOpen: () => {},
  sidebarCollapsed: false,
  setSidebarCollapsed: () => {},
});

export const useDashboard = () => useContext(DashboardContext);

/* ── Shell Component ─────────────────────────────────────── */
export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Auth Check: Redirect to login if token is missing
    const token = localStorage.getItem("wg-token");
    if (!token) {
      window.location.href = "/auth/login";
      return;
    }

    const savedTheme = localStorage.getItem("wg-theme") as "dark" | "light" | null;
    if (savedTheme) setTheme(savedTheme);
    const savedCollapsed = localStorage.getItem("wg-sidebar-collapsed") === "true";
    setSidebarCollapsed(savedCollapsed);
    setMounted(true);
  }, []);

  // Apply light-mode class to <html>
  useEffect(() => {
    if (!mounted) return;
    if (theme === "light") {
      document.documentElement.classList.add("light-mode");
    } else {
      document.documentElement.classList.remove("light-mode");
    }
  }, [theme, mounted]);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("wg-theme", next);
  }

  function handleSetSidebarCollapsed(v: boolean) {
    setSidebarCollapsed(v);
    localStorage.setItem("wg-sidebar-collapsed", String(v));
  }

  if (!mounted) {
    return (
      <div className="flex h-screen bg-cyber-bg items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <DashboardContext.Provider
      value={{
        theme,
        toggleTheme,
        sidebarOpen,
        setSidebarOpen,
        sidebarCollapsed,
        setSidebarCollapsed: handleSetSidebarCollapsed,
      }}
    >
      <div className="flex h-screen overflow-hidden bg-cyber-bg">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/60 z-20 lg:hidden backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <Sidebar />

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <TopHeader />
          <main className="flex-1 overflow-y-auto dashboard-scroll p-6 bg-cyber-bg">
            {children}
          </main>
        </div>
      </div>
    </DashboardContext.Provider>
  );
}
